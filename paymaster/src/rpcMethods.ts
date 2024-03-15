import { BigNumberish, ethers } from 'ethers';
import { paymasterAbi } from './abis';
import { BytesLike } from '@ethersproject/bytes';
import { whitelistAll, whitelistedAddresses } from './config';
import dotenv from 'dotenv';
dotenv.config();

export interface PackedUserOperation {
    sender: string
    nonce: BigNumberish
    initCode: BytesLike
    callData: BytesLike
    accountGasLimits: BytesLike
    preVerificationGas: BigNumberish
    gasFees: BytesLike
    paymasterAndData: BytesLike
    signature: BytesLike
}

export async function sponsorTransaction(userOp: PackedUserOperation): Promise<PackedUserOperation> {
    const paymasterAddress = process.env.PAYMASTER_ADDRESS as string;
    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL as string);
    const signer = new ethers.Wallet(process.env.PRIVATE_KEY as string);

    const paymaster = new ethers.Contract(
        paymasterAddress,
        paymasterAbi,
        provider
    );

    // If user address is not whitelisted for gas sponsor, return
    if (
        !whitelistAll && !whitelistedAddresses.map(
            address => address.toLowerCase()
        ).includes(userOp.sender.toLowerCase())
    ) {
        return userOp;
    }

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