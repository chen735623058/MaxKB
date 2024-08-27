# coding=utf-8
"""
    @project: MaxKB
    @Author：虎
    @file： base_function_lib_node.py
    @date：2024/8/8 17:49
    @desc:
"""
import json
import time

from typing import Dict

from application.flow.i_step_node import NodeResult
from application.flow.step_node.function_node.i_function_node import IFunctionNode
from common.exception.app_exception import AppApiException
from common.util.function_code import FunctionExecutor
from smartdoc.const import CONFIG

function_executor = FunctionExecutor(CONFIG.get('SANDBOX'))


def write_context(step_variable: Dict, global_variable: Dict, node, workflow):
    if step_variable is not None:
        for key in step_variable:
            node.context[key] = step_variable[key]
        if workflow.is_result() and 'result' in step_variable:
            result = str(step_variable['result']) + '\n'
            yield result
            workflow.answer += result
    node.context['run_time'] = time.time() - node.context['start_time']


def valid_reference_value(_type, value, name):
    if _type == 'int':
        return isinstance(value, int)
    if _type == 'float':
        return isinstance(value, float)
    if _type == 'dict':
        return isinstance(value, dict)
    if _type == 'array':
        return isinstance(value, list)
    if _type == 'string':
        return isinstance(value, str)
    raise Exception(500, f'字段:{name}类型:{_type}值:{value}类型错误')


def convert_value(name: str, value, _type, is_required, source, node):
    if not is_required and value is None:
        return None
    if source == 'reference':
        value = node.workflow_manage.get_reference_field(
            value[0],
            value[1:])
        valid_reference_value(_type, value, name)
        return value
    try:
        if _type == 'int':
            return int(value)
        if _type == 'float':
            return float(value)
        if _type == 'dict':
            v = json.loads(value)
            if isinstance(v, dict):
                return v
            raise Exception("类型错误")
        if _type == 'array':
            v = json.loads(value)
            if isinstance(v, list):
                return v
            raise Exception("类型错误")
        return value
    except Exception as e:
        raise Exception(f'字段:{name}类型:{_type}值:{value}类型错误')


class BaseFunctionNodeNode(IFunctionNode):
    def execute(self, input_field_list, code, **kwargs) -> NodeResult:
        params = {field.get('name'): convert_value(field.get('name'), field.get('value'), field.get('type'),
                                                   field.get('is_required'), field.get('source'), self)
                  for field in input_field_list}
        result = function_executor.exec_code(code, params)
        self.context['params'] = params
        return NodeResult({'result': result}, {}, _write_context=write_context)

    def get_details(self, index: int, **kwargs):
        return {
            'name': self.node.properties.get('stepName'),
            "index": index,
            "result": self.context.get('result'),
            "params": self.context.get('params'),
            'run_time': self.context.get('run_time'),
            'type': self.node.type,
            'status': self.status,
            'err_message': self.err_message
        }
