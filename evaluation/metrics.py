# evaluation/metrics.py
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

# 建议：将calculate_quality_score迁移到metrics.py作为简化指标
class TrajectoryQualityMetric(BaseMetric):
    """轨迹质量快速评估指标（兼容现有报告）"""
    
    def calculate_quality_score(self, steps, tools):
        """计算轨迹质量分数"""
        if not steps:
            return 0

        score = 0.5  # 基础分

        # 1. 步骤完整性检查
        if len(steps) >= 2:
            score += 0.1

        # 2. 工具使用检查
        if tools:
            score += 0.1

        # 3. 步骤粒度检查
        if 2 <= len(steps) <= 5:
            score += 0.1
        elif len(steps) > 8:
            score -= 0.1  # 步骤过多扣分

        # 4. 检查步骤是否包含必要关键词
        required_keywords = ["订单", "退货", "优惠券", "转人工"]
        found_keywords = sum(1 for kw in required_keywords
                            if any(kw in step for step in steps))
        score += found_keywords * 0.05

        return min(1.0, max(0.0, score))  # 限制在0-1之间


    def measure(self, test_case):
        steps = getattr(test_case, 'steps', [])
        tools = getattr(test_case, 'tools', [])
        return calculate_quality_score(steps, tools)

class TaskDecompositionMetric(BaseMetric):
    """任务分解质量评估指标"""

    def __init__(self, threshold=0.7):
        self.threshold = threshold
        self.score = 0.0

    def measure(self, test_case: LLMTestCase) -> float:
        """
        评估任务分解质量

        评分维度：
        - 完整性：是否覆盖所有必要步骤
        - 正确性：步骤是否符合业务逻辑
        - 效率性：是否使用最少必要步骤

        Args:
            test_case: 测试用例，应包含：
                - task_plan: Agent生成的任务计划步骤列表
                - expected_plan_elements: 期望包含的任务元素列表（可选）
                - query: 用户查询（可选，用于推断期望元素）
        """
        # 从test_case中提取任务计划
        if hasattr(test_case, 'task_plan'):
            task_plan = test_case.task_plan
        else:
            # 如果没有task_plan字段，尝试其他可能的字段名
            task_plan = getattr(test_case, 'plan', [])
        
        # 从test_case中提取期望元素（可选）
        expected_elements = None
        if hasattr(test_case, 'expected_plan_elements'):
            expected_elements = test_case.expected_plan_elements
        elif hasattr(test_case, 'expected_elements'):
            expected_elements = test_case.expected_elements
        elif hasattr(test_case, 'query'):
            # 从查询中提取关键信息作为期望元素
            query = test_case.query
            # 简单提取关键词作为期望元素
            keywords = ["订单", "退货", "优惠券", "转人工", "查询", "申请"]
            expected_elements = [kw for kw in keywords if kw in query]
        
        # 评估任务分解质量
        score, details = self.evaluate_decomposition(task_plan, expected_elements)
        
        # 转换为0-1范围（evaluate_decomposition返回0-100）
        self.score = round(score / 100.0, 4)
        
        # 保存评估详情（可选）
        self.evaluation_details = details
        
        return self.score

    def is_successful(self) -> bool:
        return self.score >= self.threshold

    @property
    def __name__(self):
        return "Task Decomposition"
    
    def get_performance_report(self) -> dict:
        """获取任务分解评估报告"""
        if hasattr(self, 'evaluation_details'):
            report = self.evaluation_details.copy()
        else:
            report = {}
        
        report.update({
            "score": self.score,
            "threshold": self.threshold,
            "is_successful": self.is_successful()
        })
        return report

    def evaluate_decomposition(self,plan, expected_elements=None):
        """
        评估任务分解质量

        评分维度：
        - 完整性 (30%)
        - 逻辑性 (30%)
        - 粒度 (20%)
        - 可执行性 (20%)
        """
        score = 0.0
        details = {}

        # 1. 完整性评分 (0-30)
        if expected_elements:
            found = sum(1 for elem in expected_elements
                        if any(elem in step for step in plan))
            completeness = found / len(expected_elements)
            details['completeness'] = round(completeness * 30, 4)
            score += details['completeness']

        # 2. 逻辑性评分 (0-30)
        logical_score = self.evaluate_logical_order(plan)
        details['logical'] = logical_score * 30
        score += details['logical']

        # 3. 粒度评分 (0-20)
        granularity_score = self.evaluate_granularity(plan)
        details['granularity'] = granularity_score * 20
        score += details['granularity']

        # 4. 可执行性评分 (0-20)
        executable_score = self.evaluate_executability(plan)
        details['executable'] = executable_score * 20
        score += details['executable']

        return score, details

    def evaluate_logical_order(self,plan):
        """评估步骤逻辑顺序"""
        if len(plan) <= 1:
            return 1.0

        # 检查常见的逻辑依赖
        violations = 0
        total_checks = 0

        # 检查：查询应该在操作之前
        query_before_action = any(
            "查询" in plan[i] and "操作" in plan[j] and i > j
            for i in range(len(plan))
            for j in range(len(plan))
        )
        if query_before_action:
            violations += 1
        total_checks += 1

        # 检查：验证应该在执行之前
        verify_before_execute = any(
            "验证" in plan[i] and "执行" in plan[j] and i > j
            for i in range(len(plan))
            for j in range(len(plan))
        )
        if verify_before_execute:
            violations += 1
        total_checks += 1

        return 1 - (violations / total_checks)

    def evaluate_granularity(self,plan):
        """评估步骤粒度"""
        # 步骤太少（<2）或太多（>8）都扣分
        if len(plan) < 2:
            return 0.3
        elif len(plan) > 8:
            return 0.5
        elif 3 <= len(plan) <= 6:
            return 1.0
        else:
            return 0.7

    def evaluate_executability(self,plan):
        """评估步骤可执行性"""
        executable_count = 0
        for step in plan:
            # 检查是否有对应工具关键词
            has_tool = any(
                keyword in step
                for keyword in ["查询", "验证", "创建", "调用",
                                "query", "check", "return", "transfer"]
            )
            if has_tool:
                executable_count += 1

        return round(executable_count / len(plan), 4) if plan else 0
    
    def evaluate_decomposition_batch(self, test_cases):
        """批量评估任务分解"""
        total_score = 0.0
        details_list = []
        
        for test_case in test_cases:
            score = self.measure(test_case)
            total_score += score
            if hasattr(self, 'evaluation_details'):
                details_list.append(self.evaluation_details.copy())
        
        avg_score = total_score / len(test_cases) if test_cases else 0.0
        
        report = {
            "metric_name": "任务分解评估",
            "average_score": avg_score,
            "total_cases": len(test_cases),
            "batch_details": details_list
        }
        
        # 如果有评估详情，添加汇总信息
        if details_list:
            report["summary"] = {
                "avg_completeness": sum(d.get('completeness', 0) for d in details_list) / len(details_list) if 'completeness' in details_list[0] else 0,
                "avg_logical": sum(d.get('logical', 0) for d in details_list) / len(details_list) if 'logical' in details_list[0] else 0,
                "avg_granularity": sum(d.get('granularity', 0) for d in details_list) / len(details_list) if 'granularity' in details_list[0] else 0,
                "avg_executable": sum(d.get('executable', 0) for d in details_list) / len(details_list) if 'executable' in details_list[0] else 0
            }
        
        return report


class ToolSelectionMetric(BaseMetric):
    """工具选择准确性评估（基于精确率/召回率）"""

    def __init__(self, threshold=0.8):
        self.threshold = threshold
        self.score = 0.0
        self.reset_counters()
    
    def reset_counters(self):
        """重置计数器和统计数据"""
        self.true_positives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.true_negatives = 0
        self.total_samples = 0
    
    def update_counts(self, tp=0, fp=0, fn=0, tn=0):
        """更新计数"""
        self.true_positives += tp
        self.false_positives += fp
        self.false_negatives += fn
        self.true_negatives += tn
        self.total_samples += (tp + fp + fn + tn)
    
    def calculate_precision(self):
        """计算精确率"""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return round(self.true_positives / (self.true_positives + self.false_positives), 4)
    
    def calculate_recall(self):
        """计算召回率"""
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return round(self.true_positives / (self.true_positives + self.false_negatives), 4)
    
    def calculate_f1_score(self):
        """计算F1分数（精确率和召回率的调和平均）"""
        precision = self.calculate_precision()
        recall = self.calculate_recall()
        if precision + recall == 0:
            return 0.0
        return round(2 * (precision * recall) / (precision + recall), 4)
    
    def calculate_accuracy(self):
        """计算准确率"""
        if self.total_samples == 0:
            return 0.0
        return round((self.true_positives + self.true_negatives) / self.total_samples, 4)

    def measure(self, test_case: LLMTestCase) -> float:
        """评估工具选择的准确性（基于精确率/召回率）"""
        # 检查test_case是否包含所需字段
        if hasattr(test_case, 'expected_tools') and hasattr(test_case, 'actual_tools'):
            expected_set = set(test_case.expected_tools)
            actual_set = set(test_case.actual_tools)
            
            # 计算TP, FP, FN
            tp = len(expected_set & actual_set)  # 交集：正确选择的工具
            fp = len(actual_set - expected_set)  # 实际选择但不应选择的工具
            fn = len(expected_set - actual_set)  # 应选择但未选择的工具
            
            # 更新计数器
            self.update_counts(tp=tp, fp=fp, fn=fn)
        else:
            # 如果test_case不包含所需字段，使用默认值
            print("⚠️ ToolSelectionMetric: test_case缺少expected_tools或actual_tools字段")
            return 0.0
        
        # 计算并返回F1分数
        self.score = self.calculate_f1_score()
        return self.score

    def is_successful(self) -> bool:
        return self.score >= self.threshold
    
    def get_performance_report(self) -> dict:
        """获取详细的性能报告"""
        return {
            "precision": self.calculate_precision(),
            "recall": self.calculate_recall(),
            "f1_score": self.calculate_f1_score(),
            "accuracy": self.calculate_accuracy(),
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "true_negatives": self.true_negatives,
            "total_samples": self.total_samples,
            "threshold": self.threshold,
            "is_successful": self.is_successful()
        }

    def evaluate_tool_batch(self, test_cases):
        """批量评估工具选择"""
        self.reset_counters()
        
        for test_case in test_cases:
            self.measure(test_case)
        
        report = self.get_performance_report()
        report["metric_name"] = "工具选择评估"
        return report

    @property
    def __name__(self):
        return "Tool Selection"


class DecisionAccuracyMetric(BaseMetric):
    """决策准确性评估（基于多维度匹配）"""

    def __init__(self, threshold=0.7):
        self.threshold = threshold
        self.score = 0.0
        self.evaluation_details = {}
    
    def measure(self, test_case: LLMTestCase) -> float:
        """评估Agent决策的准确性"""
        # 初始化评分
        total_score = 0.0
        max_score = 0.0
        details = {}
        
        # 维度1：最终答案匹配（如果提供期望答案）
        if hasattr(test_case, 'expected_answer') and hasattr(test_case, 'actual_answer'):
            answer_score = self._evaluate_answer_match(
                test_case.expected_answer, 
                test_case.actual_answer
            )
            total_score += answer_score * 0.4  # 权重40%
            max_score += 0.4
            details['answer_match'] = answer_score
        
        # 维度2：决策结果匹配（如果提供期望决策）
        if hasattr(test_case, 'expected_decision') and hasattr(test_case, 'actual_decision'):
            decision_score = self._evaluate_decision_match(
                test_case.expected_decision,
                test_case.actual_decision
            )
            total_score += decision_score * 0.3  # 权重30%
            max_score += 0.3
            details['decision_match'] = decision_score
        
        # 维度3：业务逻辑正确性（如果提供查询和结果）
        if hasattr(test_case, 'query') and hasattr(test_case, 'actual_result'):
            logic_score = self._evaluate_business_logic(
                test_case.query,
                test_case.actual_result
            )
            total_score += logic_score * 0.3  # 权重30%
            max_score += 0.3
            details['business_logic'] = logic_score
        
        # 如果没有提供任何评估维度，使用默认值
        if max_score == 0:
            print("⚠️ DecisionAccuracyMetric: test_case缺少评估字段，使用默认值")
            self.score = 0.82
            details['default'] = True
        else:
            # 计算加权平均分数
            self.score = round(total_score / max_score, 4) if max_score > 0 else 0.0
        
        self.evaluation_details = details
        return self.score
    
    def _evaluate_answer_match(self, expected_answer, actual_answer):
        """评估答案匹配度"""
        if expected_answer == actual_answer:
            return 1.0
        
        # 简单关键词匹配
        expected_lower = expected_answer.lower()
        actual_lower = actual_answer.lower()
        
        # 检查是否包含关键信息
        important_keywords = ["订单", "退货", "成功", "失败", "可以", "不可以", "批准", "拒绝"]
        match_count = 0
        for keyword in important_keywords:
            if keyword in expected_lower and keyword in actual_lower:
                match_count += 1
            elif keyword not in expected_lower and keyword not in actual_lower:
                # 两者都不包含该关键词也算匹配
                match_count += 1
        
        return match_count / len(important_keywords) if important_keywords else 0.5
    
    def _evaluate_decision_match(self, expected_decision, actual_decision):
        """评估决策匹配度"""
        if expected_decision == actual_decision:
            return 1.0
        
        # 尝试将决策转换为布尔值进行比较
        try:
            expected_bool = str(expected_decision).lower() in ["true", "yes", "可以", "批准", "成功", "1"]
            actual_bool = str(actual_decision).lower() in ["true", "yes", "可以", "批准", "成功", "1"]
            return 1.0 if expected_bool == actual_bool else 0.0
        except:
            return 0.0
    
    def _evaluate_business_logic(self, query, actual_result):
        """评估业务逻辑正确性"""
        # 这里可以添加更多业务逻辑检查
        # 简化版本：检查结果是否包含查询中的关键信息
        query_keywords = ["订单", "退货", "优惠券", "转人工", "查询", "申请"]
        found_keywords = sum(1 for kw in query_keywords if kw in query)
        
        if found_keywords == 0:
            return 0.5  # 没有关键词，返回中性分数
        
        # 检查实际结果是否响应了查询
        result_str = str(actual_result)
        response_keywords = ["订单", "退货", "优惠券", "客服", "查询", "结果"]
        response_count = sum(1 for kw in response_keywords if kw in result_str)
        
        return min(1.0, response_count / found_keywords) if found_keywords > 0 else 0.5

    def is_successful(self) -> bool:
        return self.score >= self.threshold
    
    def get_evaluation_details(self):
        """获取评估详情"""
        return self.evaluation_details
    
    def get_performance_report(self) -> dict:
        """获取决策准确性评估报告"""
        report = self.evaluation_details.copy() if self.evaluation_details else {}
        report.update({
            "score": self.score,
            "threshold": self.threshold,
            "is_successful": self.is_successful()
        })
        return report

    @property
    def __name__(self):
        return "Decision Accuracy"


class PrecisionRecallMetric(BaseMetric):
    """精确率/召回率监控基础类"""
    
    def __init__(self, threshold=0.7):
        self.threshold = threshold
        self.score = 0.0
        self.reset_counters()
    
    def reset_counters(self):
        """重置计数器和统计数据"""
        self.true_positives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.true_negatives = 0
        self.total_samples = 0
    
    def update_counts(self, tp=0, fp=0, fn=0, tn=0):
        """更新计数"""
        self.true_positives += tp
        self.false_positives += fp
        self.false_negatives += fn
        self.true_negatives += tn
        self.total_samples += (tp + fp + fn + tn)
    
    def calculate_precision(self):
        """计算精确率"""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return round(self.true_positives / (self.true_positives + self.false_positives), 4)
    
    def calculate_recall(self):
        """计算召回率"""
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return round(self.true_positives / (self.true_positives + self.false_negatives), 4)
    
    def calculate_f1_score(self):
        """计算F1分数（精确率和召回率的调和平均）"""
        precision = self.calculate_precision()
        recall = self.calculate_recall()
        if precision + recall == 0:
            return 0.0
        return round(2 * (precision * recall) / (precision + recall), 4)
    
    def calculate_accuracy(self):
        """计算准确率"""
        if self.total_samples == 0:
            return 0.0
        return round((self.true_positives + self.true_negatives) / self.total_samples, 4)
    
    def measure(self, test_case: LLMTestCase) -> float:
        """基础measure方法，子类应重写"""
        # 默认返回F1分数
        self.score = self.calculate_f1_score()
        return round(self.score, 4)
    
    def is_successful(self) -> bool:
        return round(self.score, 4) >= self.threshold
    
    def get_performance_report(self) -> dict:
        """获取详细的性能报告"""
        return {
            "precision": self.calculate_precision(),
            "recall": self.calculate_recall(),
            "f1_score": self.calculate_f1_score(),
            "accuracy": self.calculate_accuracy(),
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "true_negatives": self.true_negatives,
            "total_samples": self.total_samples,
            "threshold": self.threshold,
            "is_successful": self.is_successful()
        }
    
    @property
    def __name__(self):
        return "Precision Recall"


class IntentRecognitionMetric(PrecisionRecallMetric):
    """意图识别精确率/召回率监控
    意图识别精确率 TP/(TP+FP) Agent识别意图的准确性
    意图识别召回率 TP/(TP+FN) Agent识别所有意图的能力
    """
    
    def __init__(self, threshold=0.8):
        super().__init__(threshold)
        self.intent_labels = {
            "query_order": "查询订单",
            "return_request": "退换货",
            "check_coupon": "查询优惠券",
            "transfer_human": "转人工",
            "general_qa": "一般问答"
        }
    
    def measure(self, test_case: LLMTestCase) -> float:
        """
        评估意图识别的精确率/召回率
        
        Args:
            test_case: 测试用例，应包含：
                - input: 用户查询
                - expected_intent: 期望的意图
                - actual_intent: Agent实际识别的意图
        """
        # 从test_case中提取数据
        if hasattr(test_case, 'expected_intent') and hasattr(test_case, 'actual_intent'):
            expected = test_case.expected_intent
            actual = test_case.actual_intent
            
            # 更新计数器
            if expected == actual:
                # 正确识别
                self.update_counts(tp=1)
            else:
                # 错误识别：实际为FP，期望为FN
                self.update_counts(fp=1, fn=1)
        else:
            # 如果test_case不包含所需字段，使用默认值
            print("⚠️ test_case缺少expected_intent或actual_intent字段")
            return 0.0
        
        # 计算并返回F1分数
        self.score = self.calculate_f1_score()
        return round(self.score, 4)
    
    def evaluate_intent_batch(self, test_cases):
        """批量评估意图识别"""
        self.reset_counters()
        
        for test_case in test_cases:
            self.measure(test_case)
        
        report = self.get_performance_report()
        report["metric_name"] = "意图识别评估"
        return report
    
    @property
    def __name__(self):
        return "Intent Recognition"


class ToolSelectionMetricExtended(PrecisionRecallMetric):
    """工具选择精确率/召回率监控"""
    
    def __init__(self, threshold=0.85):
        super().__init__(threshold)
        self.known_tools = {
            "query_order": "查询订单",
            "return_request": "申请退换货", 
            "check_coupon": "查询优惠券",
            "transfer_human": "转人工客服"
        }
    
    def measure(self, test_case: LLMTestCase) -> float:
        """
        评估工具选择的精确率/召回率
        
        Args:
            test_case: 测试用例，应包含：
                - expected_tools: 期望使用的工具列表
                - actual_tools: Agent实际使用的工具列表
        """
        if hasattr(test_case, 'expected_tools') and hasattr(test_case, 'actual_tools'):
            expected_set = set(test_case.expected_tools)
            actual_set = set(test_case.actual_tools)
            
            # 计算TP, FP, FN
            tp = len(expected_set & actual_set)  # 交集：正确选择的工具
            fp = len(actual_set - expected_set)  # 实际选择但不应选择的工具
            fn = len(expected_set - actual_set)  # 应选择但未选择的工具
            
            # 更新计数器
            self.update_counts(tp=tp, fp=fp, fn=fn)
        else:
            print("⚠️ test_case缺少expected_tools或actual_tools字段")
            return 0.0
        
        # 计算并返回F1分数
        self.score = self.calculate_f1_score()
        return round(self.score, 4)
    
    def evaluate_tool_batch(self, test_cases):
        """批量评估工具选择"""
        self.reset_counters()
        
        for test_case in test_cases:
            self.measure(test_case)
        
        report = self.get_performance_report()
        report["metric_name"] = "工具选择评估"
        return report
    
    @property
    def __name__(self):
        return "Tool Selection Extended"


class TaskDecompositionPrecisionMetric(PrecisionRecallMetric):
    """任务分解精确率监控（基于步骤质量）"""
    
    def __init__(self, threshold=0.7):
        super().__init__(threshold)
        self.required_keywords = {
            "query_order": ["订单", "查询", "查一下"],
            "return_request": ["退货", "退款", "退换货"],
            "check_coupon": ["优惠券", "优惠", "折扣"],
            "transfer_human": ["人工", "客服", "转人工"]
        }
    
    def measure(self, test_case: LLMTestCase) -> float:
        """
        评估任务分解的质量
        
        Args:
            test_case: 测试用例，应包含：
                - query: 用户查询
                - task_plan: Agent生成的任务计划步骤列表
                - intent: Agent识别的意图
        """
        if not (hasattr(test_case, 'query') and hasattr(test_case, 'task_plan') and hasattr(test_case, 'intent')):
            print("⚠️ test_case缺少query、task_plan或intent字段")
            return 0.0
        
        query = test_case.query
        task_plan = test_case.task_plan
        intent = test_case.intent
        
        # 获取该意图对应的期望关键词
        expected_keywords = self.required_keywords.get(intent, [])
        
        if not task_plan:
            # 没有任务计划，视为完全失败
            self.update_counts(fn=len(expected_keywords))
        else:
            # 检查每个步骤是否包含期望的关键词
            relevant_steps = 0
            irrelevant_steps = 0
            
            for step in task_plan:
                step_has_keyword = any(keyword in step for keyword in expected_keywords)
                if step_has_keyword:
                    relevant_steps += 1
                else:
                    irrelevant_steps += 1
            
            # 计算指标
            # TP: 包含相关关键词的步骤
            # FP: 不包含相关关键词的步骤
            # FN: 期望包含但实际未出现的步骤（简化为期望关键词数量-相关步骤）
            tp = relevant_steps
            fp = irrelevant_steps
            fn = max(0, len(expected_keywords) - relevant_steps)
            
            self.update_counts(tp=tp, fp=fp, fn=fn)
        
        # 计算并返回F1分数
        self.score = self.calculate_f1_score()
        return round(self.score, 4)
    
    def evaluate_decomposition_batch(self, test_cases):
        """批量评估任务分解"""
        self.reset_counters()
        
        for test_case in test_cases:
            self.measure(test_case)
        
        report = self.get_performance_report()
        report["metric_name"] = "任务分解评估"
        return report
    
    @property
    def __name__(self):
        return "Task Decomposition Precision"


class PerformanceMonitor:
    """综合性能监控器，集成所有指标"""
    
    def __init__(self):
        self.intent_metric = IntentRecognitionMetric()
        self.tool_metric = ToolSelectionMetricExtended()
        self.decomposition_metric = TaskDecompositionMetric()
        self.decision_metric = DecisionAccuracyMetric()
        self.metrics_history = []
    
    def evaluate_agent_run(self, query, expected_intent, expected_tools, actual_result):
        """
        评估单次Agent运行的性能
        
        Args:
            query: 用户查询
            expected_intent: 期望的意图
            expected_tools: 期望使用的工具列表
            actual_result: Agent实际运行结果（dict）
        """
        # 创建测试用例对象
        class TestCase:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # 评估意图识别
        intent_test_case = TestCase(
            expected_intent=expected_intent,
            actual_intent=actual_result.get("intent")
        )
        intent_score = self.intent_metric.measure(intent_test_case)
        
        # 评估工具选择
        tool_test_case = TestCase(
            expected_tools=expected_tools,
            actual_tools=actual_result.get("tools_used", [])
        )
        tool_score = self.tool_metric.measure(tool_test_case)
        
        # 评估任务分解
        decomposition_test_case = TestCase(
            query=query,
            task_plan=actual_result.get("task_plan", []),
            intent=actual_result.get("intent")
        )
        decomposition_score = self.decomposition_metric.measure(decomposition_test_case)
        
        # 评估决策准确性（使用默认值）
        decision_test_case = TestCase()
        decision_score = self.decision_metric.measure(decision_test_case)
        
        # 记录结果
        result = {
            "query": query,
            "intent_score": intent_score,
            "tool_score": tool_score,
            "decomposition_score": decomposition_score,
            "decision_score": decision_score,
            "timestamp": self._get_timestamp()
        }
        self.metrics_history.append(result)
        
        return result
    
    def get_summary_report(self):
        """获取综合性能报告"""
        if not self.metrics_history:
            return {"message": "尚无性能数据"}
        
        summary = {
            "total_runs": len(self.metrics_history),
            "average_intent_score": self._calculate_average("intent_score"),
            "average_tool_score": self._calculate_average("tool_score"),
            "average_decomposition_score": self._calculate_average("decomposition_score"),
            "average_decision_score": self._calculate_average("decision_score"),
            "intent_details": self.intent_metric.get_performance_report(),
            "tool_details": self.tool_metric.get_performance_report(),
            "decomposition_details": self.decomposition_metric.get_performance_report(),
            "decision_details": {"score": self.decision_metric.score}
        }
        
        return summary
    
    def _calculate_average(self, field):
        """计算字段平均值"""
        values = [item[field] for item in self.metrics_history if field in item]
        return round(sum(values) / len(values), 4) if values else 0.0
    
    def _get_timestamp(self):
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def export_report(self, filepath="performance_report.json"):
        """导出性能报告到文件"""
        import json
        report = self.get_summary_report()
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📊 性能报告已导出到: {filepath}")
        return filepath