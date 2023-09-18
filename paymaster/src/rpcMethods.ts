import { BigNumberish, ethers } from 'ethers';
import { paymasterAbi } from './abis';
import { BytesLike } from '@ethersproject/bytes';
import dotenv from 'dotenv';
dotenv.config();

export interface UserOperation {
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

export async function sponsorTransaction(userOp: UserOperation): Promise<UserOperation> {
    const paymasterAddress = process.env.PAYMASTER_ADDRESS as string;
    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL as string);
    const signer = new ethers.Wallet(process.env.PRIVATE_KEY as string);

    const paymaster = new ethers.Contract(
        paymasterAddress,
        paymasterAbi,
        provider
    );

    /// NOTE: Define additional transaction sponsor logic here if needed
    /// For example, it could be a list of whitelisted addresses

    const coder = new ethers.AbiCoder();
    const validAfter = (await provider.getBlock('latest'))?.timestamp;
    // sanity check for validAfter
    if (validAfter === undefined) throw new Error('Could not get latest block timestamp');
    // time validity of 5 minutes by default if not set
    const validUntil = validAfter + parseInt(process.env.TIME_VALIDITY ?? '300');
    const hash = await paymaster.getHash(userOp, validUntil, validAfter);
    const signature = await signer.signMessage(ethers.getBytes(hash));

    return {
        ...userOp,
        paymasterAndData: ethers.concat([
            paymasterAddress, 
            coder.encode(
                ['uint48', 'uint48'], 
                [validUntil, validAfter]
            ), 
            signature
        ])
    }
}