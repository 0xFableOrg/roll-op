import express, { Express, Request, Response } from 'express';
import bodyParser from 'body-parser';

const app: Express = express();
const port = 3000;

app.use(bodyParser.json());

app.post('/', (req: Request, res: Response) => {
    const { id, method, params } = req.body;

    res.send({
        jsonrpc: '2.0',
        id,
        result: 'OK'
    });
});

app.listen(port, () => {
    console.log(`JSON-RPC server is running on port ${port}`);
});