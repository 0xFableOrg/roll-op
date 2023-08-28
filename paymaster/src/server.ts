import express, { Express, Request, Response } from 'express';
import bodyParser from 'body-parser';

const app = express();
const port = 3000;

app.use(bodyParser.json());

app.post('/', (req: Request, res: Response) => {
    const { id, method, params } = req.body;

    console.log(`Received request for method ${method} with params ${params}`);
    res.status(200);
});

app.listen(port, () => {
    console.log(`JSON-RPC server is running on port ${port}`);
});