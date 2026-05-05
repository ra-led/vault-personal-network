import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Pool } from 'pg';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  throw new Error('DATABASE_URL is required for production payment flow');
}

export const pool = new Pool({
  connectionString: DATABASE_URL,
  max: Number(process.env.DB_POOL_MAX || 10),
  idleTimeoutMillis: Number(process.env.DB_IDLE_TIMEOUT_MS || 10000),
  connectionTimeoutMillis: Number(process.env.DB_CONNECT_TIMEOUT_MS || 5000),
  ssl: process.env.DB_SSLMODE === 'require' ? { rejectUnauthorized: false } : undefined
});

export async function initDb() {
  const initSqlPath = path.join(__dirname, 'sql', 'init.sql');
  const initSql = fs.readFileSync(initSqlPath, 'utf8');
  await pool.query(initSql);
}

export async function closeDb() {
  await pool.end();
}
