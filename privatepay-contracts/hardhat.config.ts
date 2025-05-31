import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "@openzeppelin/hardhat-upgrades";
import "hardhat-gas-reporter";
import "solidity-coverage";
import * as dotenv from "dotenv";

dotenv.config();

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      viaIR: true, // Enable for better optimization
    },
  },
  networks: {
    hardhat: {
      chainId: 1337,
      accounts: {
        count: 20,
        accountsBalance: "10000000000000000000000", // 10000 ETH
      },
    },
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 1337,
    },
    monad: {
      url: process.env.MONAD_RPC_URL || "https://testnet-rpc.monad.xyz",
      chainId: 10143,
      accounts: process.env.MONAD_PRIVATE_KEY
        ? [process.env.MONAD_PRIVATE_KEY]
        : [],
      gas: 8000000,
      gasPrice: 50000000000, // 50 gwei - Monad testnet default
      timeout: 60000,
    },
    "monad-testnet": {
      url: "https://testnet-rpc.monad.xyz",
      chainId: 10143,
      accounts: process.env.MONAD_PRIVATE_KEY
        ? [process.env.MONAD_PRIVATE_KEY]
        : [],
      gas: 8000000,
      gasPrice: 50000000000, // 50 gwei
      timeout: 60000,
    },
  },
  etherscan: {
    apiKey: {
      monad: process.env.MONAD_ETHERSCAN_API_KEY || "dummy-key",
    },
    customChains: [
      {
        network: "monad",
        chainId: 10143,
        urls: {
          apiURL: "https://testnet-explorer.monad.xyz/api",
          browserURL: "https://testnet-explorer.monad.xyz",
        },
      },
    ],
  },
  gasReporter: {
    enabled: process.env.REPORT_GAS !== undefined,
    currency: "USD",
    gasPrice: 50, // gwei
    coinmarketcap: process.env.COINMARKETCAP_API_KEY,
  },
  typechain: {
    outDir: "typechain-types",
    target: "ethers-v6",
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
  mocha: {
    timeout: 40000,
  },
};

export default config;
