import express, { Express, Request, Response } from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import { sponsorTransaction, PackedUserOperation } from './rpcMethods';

type JsonRpcRequestBody = {
    id: number;
    method: string;
    params: PackedUserOperation;
};

const app: Express = express();
const port = 3000;

app.use(bodyParser.json());

// Use cors middleware to enable CORS
app.use(cors({ origin: '*' }));

app.post('/', async(req: Request, res: Response) => {
    const { id, method, params } = req.body as JsonRpcRequestBody;

    if (method === 'pm_sponsorUserOperation') {
        try {
            const userOp = await sponsorTransaction(params);
            res.send({
                jsonrpc: '2.0',
                id,
                result: userOp
            });
        } catch (err) {
            res.send({
                jsonrpc: '2.0',
                id,
                error: err
            });
        }
        return;
    }

    res.send({
        jsonrpc: '2.0',
        id,
        result: 'No valid reponse'
    });
});

app.listen(port, () => {
    console.log(`JSON-RPC server is running on port ${port}`);
});