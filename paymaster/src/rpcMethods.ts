import { BigNumberish, ethers } from 'ethers';
import { BytesLike } from '@ethersproject/bytes';
import dotenv from 'dotenv';
dotenv.config();

interface UserOperation {
    sender: string
    nonce: BigNumberish
    initCode: BytesLike
    callData: BytesLike
    callGasLimit: BigNumberish
    verificationGasLimit: BigNumberish
    preVerificationGas: BigNumberish
    maxFeePerGas: BigNumberish
    maxPriorityFeePerGas: BigNumberish
    paymasterAndData: BytesLike
    signature: BytesLike
}

function getUserOpHash (op: UserOperation, entryPoint: string, chainId: number | bigint): string {
    const userOpHash = ethers.solidityPackedKeccak256(
        [
            'address', 'uint256', 'bytes32', 'bytes32', 'uint256', 
            'uint256', 'uint256', 'uint256', 'uint256', 'bytes32'
        ],
        [
            op.sender, 
            op.nonce, 
            ethers.solidityPackedKeccak256(['bytes'], [op.initCode]), 
            ethers.solidityPackedKeccak256(['bytes'], [op.callData]),
            op.callGasLimit, 
            op.verificationGasLimit, 
            op.preVerificationGas, 
            op.maxFeePerGas, 
            op.maxPriorityFeePerGas,
            ethers.solidityPackedKeccak256(['bytes'], [op.paymasterAndData])
        ]
    );

    return ethers.solidityPackedKeccak256(
        ['bytes32', 'address', 'uint256'],
        [userOpHash, entryPoint, chainId]
    );
}

export async function sponsorTransaction(userOp: UserOperation) {
    const entrypointAddress = process.env.ENTRYPOINT_ADDRESS as string;
    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL as string);
    const signer = new ethers.Wallet(process.env.PRIVATE_KEY as string);

    const chainId = await provider!.getNetwork().then(net => net.chainId)
    const message = ethers.getBytes(getUserOpHash(userOp, entrypointAddress, chainId))

    return {
        ...userOp,
        signature: await signer.signMessage(message)
    }
}