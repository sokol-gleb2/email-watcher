// db.js

const { Client } = require('pg');

// Replace these with your actual AWS RDS credentials
const client = new Client({
    host: 'uoe-ai-web.cjwmgeogy81q.eu-west-2.rds.amazonaws.com',
    port: 5432,
    user: 'postgres',
    password: 'EFIcluster',
    database: 'uoe-ai-web',
    ssl: false // set to true if RDS forces SSL (e.g., AWS GovCloud or special configs)
});

async function connectToDB() {
    try {
        await client.connect();
        console.log('✅ Connected to AWS RDS PostgreSQL');
        
        // Test query
        const res = await client.query('SELECT NOW()');
        console.log('🕒 Server time:', res.rows[0]);

    } catch (err) {
        console.error('❌ Connection error:', err.stack);
    } finally {
        await client.end();
    }
}

connectToDB();