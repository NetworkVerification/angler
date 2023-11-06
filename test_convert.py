#!/usr/bin/env python3
from bast import statement as bsm
from bast import longexprs as ble
from aast import statement as asm
from aast import expression as aex
from aast import types as aty
from convert import (
    convert_routing_policy,
    convert_stmt,
    get_arg,
    unreachable,
    update_arg,
    update_arg_result,
    create_result,
)


def test_convert_return_true_statement():
    old = bsm.StaticStatement(bsm.StaticStatementType.RETURN_TRUE)
    new = convert_stmt(old)
    assert new == [
        update_arg(create_result(_value=True, _return=True), aty.EnvironmentType.RESULT)
    ]


def test_convert_exit_reject_statement():
    old = bsm.StaticStatement(bsm.StaticStatementType.EXIT_REJECT)
    new = convert_stmt(old)
    assert new == [
        update_arg(create_result(_value=False, _exit=True), aty.EnvironmentType.RESULT)
    ]


def test_convert_routing_policy_empty():
    old = []
    new = convert_routing_policy(old)
    assert new.body == [
        asm.IfStatement(
            "reset_return",
            unreachable(),
            [update_arg_result(_return=False)],
            [
                update_arg_result(
                    _fallthrough=True,
                    _value=get_arg(aty.EnvironmentType.LOCAL_DEFAULT_ACTION),
                )
            ],
        )
    ]


def test_convert_routing_policy_single():
    old: list[bsm.Statement] = [
        bsm.StaticStatement(bsm.StaticStatementType.RETURN_TRUE),
    ]
    new = convert_routing_policy(old)
    assert new.body == [
        update_arg(
            create_result(_value=True, _return=True), aty.EnvironmentType.RESULT
        ),
        asm.IfStatement(
            "reset_return",
            unreachable(),
            [update_arg_result(_return=False)],
            [
                update_arg_result(
                    _fallthrough=True,
                    _value=get_arg(aty.EnvironmentType.LOCAL_DEFAULT_ACTION),
                )
            ],
        ),
    ]


def test_convert_routing_policy_return_true_two():
    old = [
        bsm.StaticStatement(bsm.StaticStatementType.RETURN_TRUE),
        bsm.SetLocalPreference(ble.LiteralLong(200)),
    ]
    new = convert_routing_policy(old)
    assert new.body == [
        update_arg(
            create_result(_value=True, _return=True), aty.EnvironmentType.RESULT
        ),
        asm.IfStatement(
            "early_return",
            unreachable(),
            [],
            [update_arg(aex.LiteralUInt(200), aty.EnvironmentType.LP)],
        ),
        asm.IfStatement(
            "reset_return",
            unreachable(),
            [update_arg_result(_return=False)],
            [
                update_arg_result(
                    _fallthrough=True,
                    _value=get_arg(aty.EnvironmentType.LOCAL_DEFAULT_ACTION),
                )
            ],
        ),
    ]


def test_convert_routing_policy_three():
    old = [
        bsm.SetLocalPreference(ble.LiteralLong(200)),
        bsm.StaticStatement(bsm.StaticStatementType.EXIT_REJECT),
        bsm.SetLocalPreference(ble.LiteralLong(100)),
    ]
    new = convert_routing_policy(old)
    assert new.body == [
        update_arg(aex.LiteralUInt(200), aty.EnvironmentType.LP),
        asm.IfStatement(
            "early_return",
            unreachable(),
            [],
            [
                # EXIT_REJECT statement
                update_arg(
                    create_result(_value=False, _exit=True), aty.EnvironmentType.RESULT
                ),
                asm.IfStatement(
                    "early_return",
                    unreachable(),
                    [],
                    [update_arg(aex.LiteralUInt(100), aty.EnvironmentType.LP)],
                ),
            ],
        ),
        asm.IfStatement(
            "reset_return",
            unreachable(),
            [update_arg_result(_return=False)],
            [
                update_arg_result(
                    _fallthrough=True,
                    _value=get_arg(aty.EnvironmentType.LOCAL_DEFAULT_ACTION),
                )
            ],
        ),
    ]
