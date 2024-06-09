import {
  createPublicClient,
  createWalletClient,
  custom,
  hexToNumber,
  maxUint256,
} from "viem";
import { blast } from "viem/chains";
import looperAbi from "./abis/Looper.json";
import wethAbi from "./abis/weth.json";

// Use $ as shorthand for document.querySelector
const $ = document.querySelector.bind(document);

let account, transport, publicClient, walletClient;

// Addresses
const wethAddress = "0x4300000000000000000000000000000000000004";
const looperAddress = "0x2cb41A98b6b01e50308AEDD754138510e2225933";

// attempt to connect to injected window.ethereum. No connect button, direct wallet connect support, or dependency
const simpleConnect = async () => {
  let _account, _transport;
  try {
    if (!window.ethereum) throw new Error();
    [_account] = await window.ethereum.request({
      method: "eth_requestAccounts",
    });
    $("#connect-btn").innerHTML = `${_account.slice(0, 7)}...${_account.slice(
      -5
    )}`;
    _transport = custom(window.ethereum);
  } catch (error) {
    _account = "Account error";
    _transport = custom(window.ethereum);
    $("#connect-btn").innerHTML = "Connect";
  }
  return [_account, _transport];
};

// Reload on chain/accounts changed (https://docs.metamask.io/wallet/reference/provider-api/#chainchanged)
window.ethereum.on("chainChanged", (chainId) => window.location.reload());
window.ethereum.on("accountsChanges", (chainId) => window.location.reload());

window.onload = async () => {
  // Initialize wallet & wallet UI
  [account, transport] = await simpleConnect();

  walletClient = createWalletClient({
    chain: blast,
    transport,
  });

  publicClient = createPublicClient({
    batch: {
      multicall: true,
    },
    transport,
  });

  const chainId = hexToNumber(
    await window.ethereum.request({ method: "eth_chainId" })
  );

  const chainButton = $("#chain-btn");

  if (chainId !== blast.id) {
    chainButton.innerHTML = "Switch to Blast";
    chainButton.addEventListener("click", async () => {
      await walletClient.addChain({ chain: blast });
    });
  } else {
    chainButton.innerHTML = "Chain: Blast";
  }

  $("#connect-btn").addEventListener("click", () => handleConnectButtonClick());

  // Init smart contract UI
  // Loop
  const looperAllowance = await getErc20Allowance(
    wethAddress,
    account,
    looperAddress
  );
  if (looperAllowance < maxUint256) {
    $("#loop-btn").innerHTML = "Approve";

    $("#looper-form").addEventListener("submit", async (e) => {
      e.preventDefault(); // prevent immediate refresh
      await erc20Approve(wethAddress, looperAddress, maxUint256);
    });
  } else {
    $("#loop-btn").innerHTML = "Loop";

    $("#looper-form").addEventListener("submit", async (e) => {
      e.preventDefault(); // prevent immediate refresh
      const loopData = new FormData(e.target);
      const loopAmount = BigInt(loopData.get("loop-amount"));
      const numLoops = BigInt(loopData.get("num-loops"));
      const addDays = BigInt(loopData.get("add-days"));
      await loop(loopAmount, numLoops, addDays);
    });
  }

  // Unwind
  // TODO:
};

const handleConnectButtonClick = async () => {
  await simpleConnect();
};

async function getErc20Allowance(erc20Address, owner, spender) {
  const { result } = await publicClient.simulateContract({
    address: erc20Address,
    abi: wethAbi["abi"],
    functionName: "allowance",
    args: [owner, spender],
    account,
  });
  return result;
}

async function erc20Approve(erc20Address, contractAddress, approvalAmount) {
  const { request } = await publicClient.simulateContract({
    address: erc20Address,
    abi: wethAbi["abi"],
    functionName: "approve",
    args: [contractAddress, approvalAmount],
    account,
  });

  const hash = await walletClient.writeContract(request);

  const transaction = await publicClient.waitForTransactionReceipt({
    hash,
  });
}

async function loop(amount, numLoops, addDays) {
  const { request } = await publicClient.simulateContract({
    address: looperAddress,
    abi: looperAbi["abi"],
    functionName: "loop",
    args: [amount, numLoops, addDays],
    account,
  });

  const hash = await walletClient.writeContract(request);

  const transaction = await publicClient.waitForTransactionReceipt({
    hash,
  });
}
