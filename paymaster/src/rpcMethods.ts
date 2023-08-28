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

export async function sponsorTransaction(userOp: UserOperation) {
    const paymasterAddress = process.env.PAYMASTER_ADDRESS as string;
    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL as string);
    const signer = new ethers.Wallet(process.env.PRIVATE_KEY as string);

    const paymaster = new ethers.Contract(
        paymasterAddress,
        ['function getHash(UserOperation calldata userOp, uint48 validUntil, uint48 validAfter) public view returns (bytes32)']
    );

    const coder = new ethers.AbiCoder();
    const validAfter = (await provider.getBlock('latest'))?.timestamp;
    // sanity check for validAfter
    if (validAfter === undefined) throw new Error('Could not get latest block timestamp');
    const validUntil = validAfter + 300; // 5 minutes
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