"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const ethers_1 = require("ethers");
const dotenv_1 = __importDefault(require("dotenv"));
const axios_1 = __importDefault(require("axios"));
const abis_1 = require("../src/abis");
dotenv_1.default.config();
function main() {
    return __awaiter(this, void 0, void 0, function* () {
        const provider = new ethers_1.ethers.JsonRpcProvider(process.env.RPC_URL);
        const signer = new ethers_1.ethers.Wallet(process.env.PRIVATE_KEY);
        // Generate initcode
        const simpleAccountFactoryAddress = process.env.SIMPLE_ACCOUNT_FACTORY_ADDRESS;
        const simpleAccountFactory = new ethers_1.ethers.Contract(simpleAccountFactoryAddress, abis_1.simpleAccountFactoryAbi, provider);
        const initCode = ethers_1.ethers.concat([
            simpleAccountFactoryAddress,
            simpleAccountFactory.interface.encodeFunctionData("createAccount", [signer.address, 0]) // set salt as 0
        ]);
        // Generate calldata to execute a transaction
        const simpleAccountAddress = yield simpleAccountFactory.getFunction("getAddress")(signer.address, 0);
        const simpleAccount = new ethers_1.ethers.Contract(simpleAccountAddress, abis_1.simpleAccountAbi, provider);
        const to = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"; // vitalik
        const value = 0;
        const data = "0x68656c6c6f"; // "hello" encoded to utf-8 bytes
        const callData = simpleAccount.interface.encodeFunctionData("execute", [to, value, data]);
        // Construct UserOp
        const userOp = {
            sender: simpleAccountAddress,
            nonce: 0,
            initCode: initCode,
            callData: callData,
            callGasLimit: ethers_1.ethers.toBeHex(1000000),
            verificationGasLimit: ethers_1.ethers.toBeHex(4000000),
            preVerificationGas: ethers_1.ethers.toBeHex(500000),
            maxFeePerGas: ethers_1.ethers.toBeHex(1e9),
            maxPriorityFeePerGas: ethers_1.ethers.toBeHex(1e9),
            paymasterAndData: "0x00",
            signature: "0x00"
        };
        // Send UserOp to paymaster RPC server
        const paymasterRpcUrl = process.env.PAYMASTER_RPC_URL;
        const jsonRpcRequest = {
            jsonrpc: '2.0',
            method: 'pm_sponsorUserOperation',
            params: userOp,
            id: 1
        };
        const response = yield axios_1.default.post(paymasterRpcUrl, jsonRpcRequest, {
            headers: {
                'Content-Type': 'application/json',
            },
        });
        console.log("Response: ", response.data.result);
    });
}
main();
