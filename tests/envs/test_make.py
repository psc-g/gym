"""Tests that gym.make works as expected."""

import re

import pytest

import gym
from gym.envs.classic_control import cartpole
from gym.wrappers import AutoResetWrapper, OrderEnforcing, TimeLimit
from gym.wrappers.env_checker import PassiveEnvChecker
from tests.envs.utils import all_testing_env_specs
from tests.envs.utils_envs import ArgumentEnv, RegisterDuringMakeEnv
from tests.wrappers.utils import has_wrapper

gym.register(
    "RegisterDuringMakeEnv-v0",
    entry_point="tests.envs.utils_envs:RegisterDuringMakeEnv",
)

gym.register(
    id="test.ArgumentEnv-v0",
    entry_point="tests.envs.utils_envs:ArgumentEnv",
    kwargs={
        "arg1": "arg1",
        "arg2": "arg2",
    },
)


def test_make():
    env = gym.make("CartPole-v1", disable_env_checker=True)
    assert env.spec.id == "CartPole-v1"
    assert isinstance(env.unwrapped, cartpole.CartPoleEnv)
    env.close()


def test_make_deprecated():
    with pytest.raises(
        gym.error.Error,
        match=re.escape(
            "Environment version v0 for `Humanoid` is deprecated. Please use `Humanoid-v4` instead."
        ),
    ):
        gym.make("Humanoid-v0", disable_env_checker=True)


def test_make_max_episode_steps():
    # Default, uses the spec's
    env = gym.make("CartPole-v1", disable_env_checker=True)
    assert has_wrapper(env, TimeLimit)
    assert (
        env.spec.max_episode_steps == gym.envs.registry["CartPole-v1"].max_episode_steps
    )
    env.close()

    # Custom max episode steps
    env = gym.make("CartPole-v1", max_episode_steps=100, disable_env_checker=True)
    assert has_wrapper(env, TimeLimit)
    assert env.spec.max_episode_steps == 100
    env.close()

    # Env spec has no max episode steps
    assert gym.spec("test.ArgumentEnv-v0").max_episode_steps is None
    env = gym.make(
        "test.ArgumentEnv-v0", arg1=None, arg2=None, arg3=None, disable_env_checker=True
    )
    assert has_wrapper(env, TimeLimit) is False
    env.close()


def test_gym_make_autoreset():
    """Tests that `gym.make` autoreset wrapper is applied only when `gym.make(..., autoreset=True)`."""
    env = gym.make("CartPole-v1", disable_env_checker=True)
    assert has_wrapper(env, AutoResetWrapper) is False
    env.close()

    env = gym.make("CartPole-v1", autoreset=False, disable_env_checker=True)
    assert has_wrapper(env, AutoResetWrapper) is False
    env.close()

    env = gym.make("CartPole-v1", autoreset=True)
    assert has_wrapper(env, AutoResetWrapper)
    env.close()


def test_make_disable_env_checker():
    """Tests that `gym.make` disable env checker is applied only when `gym.make(..., disable_env_checker=False)`."""
    env = gym.make("CartPole-v1")
    assert has_wrapper(env, PassiveEnvChecker)
    env.close()

    env = gym.make("CartPole-v1", disable_env_checker=False)
    assert has_wrapper(env, PassiveEnvChecker)
    env.close()

    env = gym.make("CartPole-v1", disable_env_checker=True)
    assert has_wrapper(env, PassiveEnvChecker) is False
    env.close()


def test_make_order_enforcing():
    """Checks that gym.make wrappers the environment with the OrderEnforcing wrapper."""
    assert all(spec.order_enforce is True for spec in all_testing_env_specs)

    env = gym.make("CartPole-v1", disable_env_checker=True)
    assert has_wrapper(env, OrderEnforcing)
    # We can assume that there all other specs will also have the order enforcing
    env.close()

    gym.register(
        id="test.OrderlessArgumentEnv-v0",
        entry_point="tests.envs.utils_envs:ArgumentEnv",
        order_enforce=False,
        kwargs={"arg1": None, "arg2": None, "arg3": None},
    )

    env = gym.make("test.OrderlessArgumentEnv-v0", disable_env_checker=True)
    assert has_wrapper(env, OrderEnforcing) is False
    env.close()


def test_make_render_mode():
    env = gym.make("CartPole-v1", disable_env_checker=True)
    assert env.render_mode is None
    env.close()

    env = gym.make("CartPole-v1", render_mode=None, disable_env_checker=True)
    assert env.render_mode is None
    valid_render_modes = env.metadata["render_modes"]
    env.close()

    assert "no mode" not in valid_render_modes
    with pytest.raises(
        gym.error.Error,
        match=re.escape(
            "Invalid render_mode provided: no mode. Valid render_modes: None, human, rgb_array, single_rgb_array"
        ),
    ):
        gym.make("CartPole-v1", render_mode="no mode", disable_env_checker=True)

    assert len(valid_render_modes) > 0
    with pytest.warns(None) as warnings:
        env = gym.make(
            "CartPole-v1", render_mode=valid_render_modes[0], disable_env_checker=True
        )
        assert env.render_mode == valid_render_modes[0]
        env.close()

    assert len(warnings) == 0


def test_make_kwargs():
    env = gym.make(
        "test.ArgumentEnv-v0",
        arg2="override_arg2",
        arg3="override_arg3",
        disable_env_checker=True,
    )
    assert env.spec.id == "test.ArgumentEnv-v0"
    assert isinstance(env.unwrapped, ArgumentEnv)
    assert env.arg1 == "arg1"
    assert env.arg2 == "override_arg2"
    assert env.arg3 == "override_arg3"
    env.close()


def test_import_module_during_make():
    # Test custom environment which is registered at make
    env = gym.make(
        "tests.envs.utils:RegisterDuringMakeEnv-v0",
        disable_env_checker=True,
    )
    assert isinstance(env.unwrapped, RegisterDuringMakeEnv)
    env.close()
