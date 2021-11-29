from brownie import network, exceptions
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    INITIAL_PRICE_FEED_VALUE,
    DECIMALS,
    get_account,
    get_contract,
)
import pytest
from scripts.deploy import KEPT_BALANCE, deploy_token_farm_and_gollux_token


def test_set_price_feed_contract():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, gollux_token = deploy_token_farm_and_gollux_token()
    # Act
    price_feed_address = get_contract("eth_usd_price_feed")
    token_farm.setPriceFeedContract(
        gollux_token.address, price_feed_address, {"from": account}
    )
    # Assert
    assert token_farm.tokenPriceFeedMapping(gollux_token.address) == price_feed_address
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.setPriceFeedContract(
            gollux_token.address, price_feed_address, {"from": non_owner}
        )


def test_stake_tokens(amount_staked, notOwner=False):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    if notOwner:
        account = get_account(index=1)
    token_farm, gollux_token = deploy_token_farm_and_gollux_token()
    # Act
    gollux_token.approve(token_farm.address, amount_staked, {"from": account})
    token_farm.stakeTokens(amount_staked, gollux_token.address, {"from": account})
    # Assert
    assert (
        token_farm.stakingBalance(gollux_token.address, account.address) == amount_staked
    )
    assert token_farm.uniqueTokensStaked(account.address) == 1
    assert token_farm.stakers(0) == account.address
    return token_farm, gollux_token


def test_issue_single_token(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token_farm, gollux_token = test_stake_tokens(amount_staked)
    starting_balance = gollux_token.balanceOf(account.address)
    print('starting_balance = ', starting_balance)
    # Act
    token_farm.issueSingleToken(account.address, {"from": account})
    # Arrange
    # we are staking 1 gollux_token == in price to 1 ETH
    # soo... we should get 2,000 dapp tokens in reward
    # since the price of eth is $2,000
    assert (
        gollux_token.balanceOf(account.address)
        == starting_balance + 1000000000000000000
    )


def test_issue_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account(index=1)
    token_farm, gollux_token = test_stake_tokens(amount_staked, True)
    starting_balance = gollux_token.balanceOf(account.address)
    print('starting_balance = ', starting_balance)
    # Act
    token_farm.issueTokens({"from": account})
    # Arrange
    # we are staking 1 gollux_token == in price to 1 ETH
    # soo... we should get 2,000 dapp tokens in reward
    # since the price of eth is $2,000
    assert (
        gollux_token.balanceOf(account.address)
        == starting_balance + INITIAL_PRICE_FEED_VALUE
    )


def test_get_user_total_value_with_different_tokens(amount_staked, random_erc20):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token_farm, gollux_token = test_stake_tokens(amount_staked)
    # Act
    token_farm.addAllowedTokens(random_erc20.address, {"from": account})
    token_farm.setPriceFeedContract(
        random_erc20.address, get_contract("eth_usd_price_feed"), {"from": account}
    )
    random_erc20_stake_amount = amount_staked * 2
    random_erc20.approve(
        token_farm.address, random_erc20_stake_amount, {"from": account}
    )
    token_farm.stakeTokens(
        random_erc20_stake_amount, random_erc20.address, {"from": account}
    )
    # Assert
    total_value = token_farm.getUserTotalValue(account.address)
    assert total_value == INITIAL_PRICE_FEED_VALUE * 3


def test_get_token_value():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    token_farm, gollux_token = deploy_token_farm_and_gollux_token()
    # Act / Assert
    assert token_farm.getTokenValue(gollux_token.address) == (
        INITIAL_PRICE_FEED_VALUE,
        DECIMALS,
    )


def test_unstake_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token_farm, gollux_token = test_stake_tokens(amount_staked)
    # Act
    token_farm.unstakeTokens(gollux_token.address, {"from": account})
    assert gollux_token.balanceOf(account.address) == KEPT_BALANCE
    assert token_farm.stakingBalance(gollux_token.address, account.address) == 0
    assert token_farm.uniqueTokensStaked(account.address) == 0


def test_add_allowed_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, gollux_token = deploy_token_farm_and_gollux_token()
    # Act
    token_farm.addAllowedTokens(gollux_token.address, {"from": account})
    # Assert
    assert token_farm.allowedTokens(0) == gollux_token.address
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.addAllowedTokens(gollux_token.address, {"from": non_owner})