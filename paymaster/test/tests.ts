import { ethers } from 'ethers';
import dotenv from 'dotenv';
import axios from 'axios';
import { UserOperation } from '../src/rpcMethods';
import { simpleAccountAbi, simpleAccountFactoryAbi, paymasterAbi, entrypointAbi } from '../src/abis';
dotenv.config();

async function main() {
    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL as string);
    const signer = new ethers.Wallet(process.env.PRIVATE_KEY as string, provider);

    // Initialize paymaster contract
    const paymasterAddress = process.env.PAYMASTER_ADDRESS as string;
    const paymaster = new ethers.Contract(
        paymasterAddress,
        paymasterAbi,
        provider
    );

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
    let userOp: UserOperation = {
        sender: simpleAccountAddress,
        nonce: Number(await paymaster.senderNonce(simpleAccountAddress)),
        initCode: initCode,
        callData: callData,
        callGasLimit: ethers.toBeHex(3_000_000), // hardcode it for now at a high value,
        verificationGasLimit: ethers.toBeHex(3_000_000), // hardcode it for now at a high value,
        preVerificationGas: ethers.toBeHex(2_000_000), // hardcode it for now at a high value,
        maxFeePerGas: ethers.toBeHex(2e9),
        maxPriorityFeePerGas: ethers.toBeHex(1e9),
        paymasterAndData: ethers.concat([
            paymasterAddress,
            '0x' + '00'.repeat(64),
            '0x' + '00'.repeat(65)
        ]),
        signature: '0x' + '00'.repeat(65)
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
    userOp = response.data.result;

    // User to sign UserOp
    const entrypointAddress = process.env.ENTRYPOINT_ADDRESS as string;
    const entrypoint = new ethers.Contract(
        entrypointAddress,
        entrypointAbi,
        provider
    );
    const userOpHash = await entrypoint.getUserOpHash(userOp);
    const signature = await signer.signMessage(ethers.getBytes(userOpHash));
    userOp = {
        ...userOp,
        signature: signature
    }
    console.log("Finalized userOp: ", userOp);

    // Estimate gas requred
    const gasEstimationRequest = {
        jsonrpc: '2.0',
        method: 'eth_estimateUserOperationGas',
        params: [userOp, entrypointAddress],
        id: 2
    }
    const gasEstimationResult = await axios.post("http://localhost:4337", gasEstimationRequest, {
        headers: {
          'Content-Type': 'application/json',
        },
    });
    console.log("Gas estimation result: ", gasEstimationResult.data.result);

    // Send UserOperation
    const userOperationRequest = {
        jsonrpc: '2.0',
        method: 'eth_sendUserOperation',
        params: [userOp, entrypointAddress],
        id: 2
    }
    const userOperationResult = await axios.post("http://localhost:4337", userOperationRequest, {
        headers: {
          'Content-Type': 'application/json',
        },
    });
    console.log("Result (userOpHash): ", userOperationResult.data.result);
}

main();