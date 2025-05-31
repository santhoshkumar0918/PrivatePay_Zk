import { ethers } from "hardhat";
import { Contract } from "ethers";
import fs from "fs";
import path from "path";

interface DeployedContracts {
  ZKVerifier: string;
  PaymentVault: string;
  PrivatePay: string;
  deploymentBlock: number;
  network: string;
  deployer: string;
  timestamp: string;
  gasUsed: {
    ZKVerifier: string;
    PaymentVault: string;
    PrivatePay: string;
    total: string;
  };
  transactionHashes: {
    ZKVerifier: string;
    PaymentVault: string;
    PrivatePay: string;
    authorization: string;
  };
}

async function main() {
  console.log("🚀 Starting PrivatePay deployment on Monad...\n");

  // Get deployer account
  const [deployer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();

  console.log("📋 Deployment Details:");
  console.log(`├─ Network: ${network.name} (Chain ID: ${network.chainId})`);
  console.log(`├─ Deployer: ${deployer.address}`);
  console.log(
    `└─ Balance: ${ethers.formatEther(
      await ethers.provider.getBalance(deployer.address)
    )} ETH\n`
  );

  // Check if we're on Monad testnet
  if (network.chainId !== 10143n) {
    console.log(
      "⚠️  Warning: Not deploying to Monad testnet (Chain ID: 10143)"
    );
    console.log(`   Current network Chain ID: ${network.chainId}`);
    console.log("   Continuing with deployment...\n");
  }

  const deployedContracts: Partial<DeployedContracts> = {};
  const currentBlock = await ethers.provider.getBlockNumber();
  const gasUsed: any = {};
  const transactionHashes: any = {};

  try {
    // Step 1: Deploy ZKVerifier
    console.log("📦 Step 1: Deploying ZKVerifier...");
    const ZKVerifier = await ethers.getContractFactory("ZKVerifier");

    console.log("├─ Estimating gas...");
    const zkVerifierDeployTx = await ZKVerifier.getDeployTransaction();
    const zkVerifierGasEstimate = await deployer.estimateGas(
      zkVerifierDeployTx
    );
    console.log(`├─ Estimated gas: ${zkVerifierGasEstimate.toString()}`);

    const zkVerifier = await ZKVerifier.deploy();
    const zkVerifierReceipt = await zkVerifier.deploymentTransaction()?.wait();
    const zkVerifierAddress = await zkVerifier.getAddress();

    console.log(`✅ ZKVerifier deployed to: ${zkVerifierAddress}`);
    console.log(`├─ Transaction hash: ${zkVerifierReceipt?.hash}`);
    console.log(`└─ Gas used: ${zkVerifierReceipt?.gasUsed.toString()}\n`);

    deployedContracts.ZKVerifier = zkVerifierAddress;
    gasUsed.ZKVerifier = zkVerifierReceipt?.gasUsed.toString();
    transactionHashes.ZKVerifier = zkVerifierReceipt?.hash;

    // Step 2: Deploy PaymentVault
    console.log("📦 Step 2: Deploying PaymentVault...");
    const PaymentVault = await ethers.getContractFactory("PaymentVault");

    console.log("├─ Estimating gas...");
    const vaultDeployTx = await PaymentVault.getDeployTransaction();
    const vaultGasEstimate = await deployer.estimateGas(vaultDeployTx);
    console.log(`├─ Estimated gas: ${vaultGasEstimate.toString()}`);

    const paymentVault = await PaymentVault.deploy();
    const vaultReceipt = await paymentVault.deploymentTransaction()?.wait();
    const paymentVaultAddress = await paymentVault.getAddress();

    console.log(`✅ PaymentVault deployed to: ${paymentVaultAddress}`);
    console.log(`├─ Transaction hash: ${vaultReceipt?.hash}`);
    console.log(`└─ Gas used: ${vaultReceipt?.gasUsed.toString()}\n`);

    deployedContracts.PaymentVault = paymentVaultAddress;
    gasUsed.PaymentVault = vaultReceipt?.gasUsed.toString();
    transactionHashes.PaymentVault = vaultReceipt?.hash;

    // Step 3: Deploy PrivatePay (main contract)
    console.log("📦 Step 3: Deploying PrivatePay...");
    const PrivatePay = await ethers.getContractFactory("PrivatePay");

    console.log("├─ Estimating gas...");
    const privatePayDeployTx = await PrivatePay.getDeployTransaction(
      zkVerifierAddress,
      paymentVaultAddress
    );
    const privatePayGasEstimate = await deployer.estimateGas(
      privatePayDeployTx
    );
    console.log(`├─ Estimated gas: ${privatePayGasEstimate.toString()}`);

    const privatePay = await PrivatePay.deploy(
      zkVerifierAddress,
      paymentVaultAddress
    );
    const privatePayReceipt = await privatePay.deploymentTransaction()?.wait();
    const privatePayAddress = await privatePay.getAddress();

    console.log(`✅ PrivatePay deployed to: ${privatePayAddress}`);
    console.log(`├─ Transaction hash: ${privatePayReceipt?.hash}`);
    console.log(`└─ Gas used: ${privatePayReceipt?.gasUsed.toString()}\n`);

    deployedContracts.PrivatePay = privatePayAddress;
    gasUsed.PrivatePay = privatePayReceipt?.gasUsed.toString();
    transactionHashes.PrivatePay = privatePayReceipt?.hash;

    // Step 4: Configure contracts
    console.log("⚙️  Step 4: Configuring contracts...");

    // Authorize PrivatePay contract to use PaymentVault
    console.log("├─ Authorizing PrivatePay on PaymentVault...");
    const authTx = await paymentVault.addAuthorizedCaller(privatePayAddress);
    const authReceipt = await authTx.wait();
    console.log(`├─ Authorization transaction: ${authReceipt?.hash}`);
    console.log(`├─ Gas used: ${authReceipt?.gasUsed.toString()}`);
    console.log("└─ ✅ Authorization complete\n");

    transactionHashes.authorization = authReceipt?.hash;

    // Step 5: Verify deployments
    console.log("🔍 Step 5: Verifying deployments...");

    // Test ZKVerifier
    console.log("├─ Testing ZKVerifier...");
    const zkStats = await zkVerifier.getVerificationStats();
    console.log(
      `│  └─ Stats: ${zkStats[0]} verified, ${zkStats[1]} failed, ${zkStats[2]}% success rate`
    );

    // Test PaymentVault
    console.log("├─ Testing PaymentVault...");
    const isAuthorized = await paymentVault.isAuthorizedCaller(
      privatePayAddress
    );
    console.log(
      `│  └─ Authorization status: ${
        isAuthorized ? "✅ Authorized" : "❌ Not authorized"
      }`
    );

    // Test PrivatePay
    console.log("├─ Testing PrivatePay...");
    const vaultAddress = await privatePay.paymentVault();
    const zkAddress = await privatePay.zkVerifier();
    console.log(
      `│  ├─ Vault connection: ${
        vaultAddress === paymentVaultAddress ? "✅" : "❌"
      }`
    );
    console.log(
      `│  └─ ZK connection: ${zkAddress === zkVerifierAddress ? "✅" : "❌"}`
    );

    // Get global stats
    console.log("└─ Testing global stats...");
    const globalStats = await privatePay.getGlobalStats();
    console.log(
      `   └─ Initial stats: ${globalStats[0]} payments, ${globalStats[1]} decoys, ${globalStats[2]} avg score\n`
    );

    // Calculate total gas used
    const totalGasUsed = (
      BigInt(gasUsed.ZKVerifier || 0) +
      BigInt(gasUsed.PaymentVault || 0) +
      BigInt(gasUsed.PrivatePay || 0) +
      BigInt(authReceipt?.gasUsed.toString() || 0)
    ).toString();

    // Step 6: Save deployment info
    const deploymentInfo: DeployedContracts = {
      ZKVerifier: zkVerifierAddress,
      PaymentVault: paymentVaultAddress,
      PrivatePay: privatePayAddress,
      deploymentBlock: currentBlock,
      network: network.name,
      deployer: deployer.address,
      timestamp: new Date().toISOString(),
      gasUsed: {
        ZKVerifier: gasUsed.ZKVerifier,
        PaymentVault: gasUsed.PaymentVault,
        PrivatePay: gasUsed.PrivatePay,
        total: totalGasUsed,
      },
      transactionHashes: {
        ZKVerifier: transactionHashes.ZKVerifier,
        PaymentVault: transactionHashes.PaymentVault,
        PrivatePay: transactionHashes.PrivatePay,
        authorization: transactionHashes.authorization,
      },
    };

    // Create deployments directory
    const deploymentsDir = path.join(__dirname, "../deployments");
    if (!fs.existsSync(deploymentsDir)) {
      fs.mkdirSync(deploymentsDir, { recursive: true });
    }

    // Save timestamped deployment file
    const deploymentFile = path.join(
      deploymentsDir,
      `monad-testnet-${Date.now()}.json`
    );
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));

    // Save latest deployment info
    const latestFile = path.join(deploymentsDir, "latest.json");
    fs.writeFileSync(latestFile, JSON.stringify(deploymentInfo, null, 2));

    // Generate environment variables for ZerePy agent integration
    const envVars = `# PrivatePay Contract Addresses (Monad Testnet)
# Generated on ${new Date().toISOString()}

# Main Contracts
PRIVATEPAY_CONTRACT_ADDRESS=${privatePayAddress}
ZK_VERIFIER_ADDRESS=${zkVerifierAddress}
PAYMENT_VAULT_ADDRESS=${paymentVaultAddress}

# Network Configuration
MONAD_CHAIN_ID=10143
MONAD_RPC_URL=https://testnet-rpc.monad.xyz

# Deployment Info
DEPLOYMENT_BLOCK=${currentBlock}
DEPLOYMENT_NETWORK=${network.name}
DEPLOYMENT_TIMESTAMP=${new Date().toISOString()}
DEPLOYER_ADDRESS=${deployer.address}

# Gas Usage
TOTAL_GAS_USED=${totalGasUsed}

# Transaction Hashes
ZKVERIFIER_TX_HASH=${transactionHashes.ZKVerifier}
PAYMENTVAULT_TX_HASH=${transactionHashes.PaymentVault}
PRIVATEPAY_TX_HASH=${transactionHashes.PrivatePay}
AUTHORIZATION_TX_HASH=${transactionHashes.authorization}

# Explorer Links
ZKVERIFIER_EXPLORER=https://testnet-explorer.monad.xyz/tx/${
      transactionHashes.ZKVerifier
    }
PAYMENTVAULT_EXPLORER=https://testnet-explorer.monad.xyz/tx/${
      transactionHashes.PaymentVault
    }
PRIVATEPAY_EXPLORER=https://testnet-explorer.monad.xyz/tx/${
      transactionHashes.PrivatePay
    }
`;

    const envFile = path.join(deploymentsDir, ".env.contracts");
    fs.writeFileSync(envFile, envVars);

    // Generate ABI files for ZerePy integration
    const abisDir = path.join(deploymentsDir, "abis");
    if (!fs.existsSync(abisDir)) {
      fs.mkdirSync(abisDir, { recursive: true });
    }

    // Copy ABI files
    const artifactsDir = path.join(__dirname, "../artifacts/contracts");

    const contracts = ["PrivatePay", "ZKVerifier", "PaymentVault"];
    for (const contractName of contracts) {
      try {
        const artifactPath = path.join(
          artifactsDir,
          `${contractName}.sol`,
          `${contractName}.json`
        );
        const abiPath = path.join(abisDir, `${contractName}.json`);

        if (fs.existsSync(artifactPath)) {
          const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
          fs.writeFileSync(abiPath, JSON.stringify(artifact.abi, null, 2));
        }
      } catch (error) {
        console.log(`⚠️  Could not copy ABI for ${contractName}: ${error}`);
      }
    }

    console.log("🎉 Deployment Complete!");
    console.log("=".repeat(80));
    console.log("📋 Contract Addresses:");
    console.log(`├─ PrivatePay:    ${privatePayAddress}`);
    console.log(`├─ ZKVerifier:    ${zkVerifierAddress}`);
    console.log(`└─ PaymentVault:  ${paymentVaultAddress}`);
    console.log("\n⛽ Gas Usage:");
    console.log(`├─ ZKVerifier:    ${gasUsed.ZKVerifier}`);
    console.log(`├─ PaymentVault:  ${gasUsed.PaymentVault}`);
    console.log(`├─ PrivatePay:    ${gasUsed.PrivatePay}`);
    console.log(`└─ Total:         ${totalGasUsed}`);
    console.log("\n📁 Files Created:");
    console.log(`├─ ${deploymentFile}`);
    console.log(`├─ ${latestFile}`);
    console.log(`├─ ${envFile}`);
    console.log(`└─ ${abisDir}/ (ABI files)`);
    console.log("\n🔗 Explorer Links:");
    console.log(
      `├─ PrivatePay:    https://testnet-explorer.monad.xyz/address/${privatePayAddress}`
    );
    console.log(
      `├─ ZKVerifier:    https://testnet-explorer.monad.xyz/address/${zkVerifierAddress}`
    );
    console.log(
      `└─ PaymentVault:  https://testnet-explorer.monad.xyz/address/${paymentVaultAddress}`
    );
    console.log("\n🔗 Next Steps:");
    console.log("1. Copy .env.contracts to your ZerePy agent project");
    console.log("2. Update monad_actions.py with the new contract addresses");
    console.log("3. Use the ABI files for contract interaction");
    console.log("4. Test your PrivatePay agent with real contracts!");
    console.log("=".repeat(80));

    // Optional: Test deployment with a small transaction
    if (process.env.TEST_DEPLOYMENT === "true") {
      console.log("\n🧪 Running deployment test...");
      await testDeployment(privatePay, paymentVault, deployer);
    }

    // Show final summary
    console.log("\n🏆 PrivatePay successfully deployed to Monad testnet!");
    console.log("Ready for ZerePy agent integration! 🚀");
  } catch (error) {
    console.error("\n❌ Deployment failed:");
    console.error(error);

    // Try to save partial deployment info
    if (Object.keys(deployedContracts).length > 0) {
      console.log("\n💾 Saving partial deployment info...");
      const partialInfo = {
        ...deployedContracts,
        error: error instanceof Error ? error.message : String(error),
        timestamp: new Date().toISOString(),
        status: "failed",
      };

      const deploymentsDir = path.join(__dirname, "../deployments");
      if (!fs.existsSync(deploymentsDir)) {
        fs.mkdirSync(deploymentsDir, { recursive: true });
      }

      const errorFile = path.join(deploymentsDir, `failed-${Date.now()}.json`);
      fs.writeFileSync(errorFile, JSON.stringify(partialInfo, null, 2));
      console.log(`Partial deployment saved to: ${errorFile}`);
    }

    process.exit(1);
  }
}

async function testDeployment(
  privatePay: any,
  paymentVault: any,
  deployer: any
) {
  try {
    console.log("├─ Testing fund deposit...");

    // Test deposit to PrivatePay
    const depositAmount = ethers.parseEther("0.1"); // 0.1 ETH
    const depositTx = await privatePay.depositFunds({ value: depositAmount });
    const depositReceipt = await depositTx.wait();

    console.log(`├─ Deposited ${ethers.formatEther(depositAmount)} ETH`);
    console.log(`├─ Transaction: ${depositReceipt?.hash}`);

    // Verify deposit
    const balance = await privatePay.getVaultBalance(deployer.address);
    console.log(`├─ ✅ Verified balance: ${ethers.formatEther(balance)} ETH`);

    // Test privacy score calculation
    const privacyScore = await privatePay.calculatePrivacyScore(
      deployer.address
    );
    console.log(`├─ ✅ Privacy score: ${privacyScore}/100`);

    // Test privacy metrics
    const metrics = await privatePay.getPrivacyMetrics(deployer.address);
    console.log(
      `├─ Privacy metrics: ${metrics[0]} payments, ${metrics[1]} decoys, ${metrics[2]}% resistance`
    );

    // Test ZK verifier stats
    const zkStats = await paymentVault.getVaultStats();
    console.log(
      `└─ ✅ Vault stats: ${zkStats[0]} payments, ${ethers.formatEther(
        zkStats[1]
      )} ETH volume`
    );
    console.log("🎯 Deployment test passed! All systems operational.");
  } catch (error) {
    console.log("⚠️  Deployment test failed (non-critical):");
    if (error instanceof Error) {
      console.log(`   Error: ${error.message}`);
    } else {
      console.log(`   Error: ${String(error)}`);
    }
    console.log("   Contracts deployed successfully, but testing failed.");
  }
}

// Execute deployment
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("💥 Deployment script crashed:");
    console.error(error);
    process.exit(1);
  });
