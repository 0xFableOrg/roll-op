import { ethers } from 'ethers';
import dotenv from 'dotenv';
import axios from 'axios';
import { UserOperation } from '../src/rpcMethods';
import { simpleAccountAbi, simpleAccountFactoryAbi } from '../src/abis';
dotenv.config();

async function main() {
    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL as string);
    const signer = new ethers.Wallet(process.env.PRIVATE_KEY as string);

    // Generate initcode
    const simpleAccountFactoryAddress = process.env.SIMPLE_ACCOUNT_FACTORY_ADDRESS as string;
    const simpleAccountFactory = new ethers.Contract(
        simpleAccountFactoryAddress,
        simpleAccountFactoryAbi,
        provider
    )
    const initCode = ethers.concat([
        simpleAccountFactoryAddress,
        simpleAccountFactory.interface.encodeFunctionData("createAccount", [signer.address, 0]) // set salt as 0
    ]);

    // Generate calldata to execute a transaction
    const simpleAccountAddress = await simpleAccountFactory.getFunction("getAddress")(signer.address, 0);
    const simpleAccount = new ethers.Contract(
        simpleAccountAddress,
        simpleAccountAbi,
        provider
    )
    const to = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" // vitalik
    const value = 0
    const data = "0x68656c6c6f" // "hello" encoded to utf-8 bytes
    const callData = simpleAccount.interface.encodeFunctionData("execute", [to, value, data]);

    // Construct UserOp
    const userOp: UserOperation = {
        sender: simpleAccountAddress,
        nonce: 0,
        initCode: initCode,
        callData: callData,
        callGasLimit: ethers.toBeHex(1_000_000), // hardcode it for now at a high value,
        verificationGasLimit: ethers.toBeHex(4_000_000), // hardcode it for now at a high value,
        preVerificationGas: ethers.toBeHex(500_000), // hardcode it for now at a high value,
        maxFeePerGas: ethers.toBeHex(1e9),
        maxPriorityFeePerGas: ethers.toBeHex(1e9),
        paymasterAndData: "0x00",
        signature: "0x00"
    }

    // Send UserOp to paymaster RPC server
    const paymasterRpcUrl = process.env.PAYMASTER_RPC_URL as string;
    const jsonRpcRequest = {
        jsonrpc: '2.0',
        method: 'pm_sponsorUserOperation',
        params: userOp,
        id: 1
    };
    const response = await axios.post(paymasterRpcUrl, jsonRpcRequest, {
        headers: {
          'Content-Type': 'application/json',
        },
    });
    console.log("Response: ", response.data.result);
}

main();