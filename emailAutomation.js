import 'dotenv/config';
import Imap from 'imap';
import { simpleParser } from 'mailparser';
import axios from 'axios';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { v4 as uuidv4 } from 'uuid';

// Helpers for __dirname in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Python environment and script
const pythonScriptPath = path.resolve(__dirname, '../parser', 'formScript.py');
const venvActivate = path.resolve(__dirname, '../parser', '.venv/bin/activate');

// IMAP Setup
const imap = new Imap({
  user: process.env.EMAIL_USER,
  password: process.env.EMAIL_PASS,
  host: process.env.IMAP_HOST,
  port: 993,
  tls: true,
  tlsOptions: { rejectUnauthorized: false }
});

function openInbox(cb) {
  imap.openBox('INBOX', false, cb);
}

let nextUid = null;

imap.once('ready', function () {
  openInbox(function (err, box) {
    if (err) {
      console.error('❌ Failed to open inbox:', err);
      return;
    }

    console.log('✅ IMAP connected. Watching for new emails...');
    nextUid = box.uidnext;

    imap.on('mail', function () {
      if (!nextUid) return;

      const fetch = imap.fetch(`${nextUid}:*`, { bodies: '', struct: true });

      fetch.on('message', msg => {
        let rawEmail = '';

        msg.on('body', stream => {
          stream.on('data', chunk => {
            rawEmail += chunk.toString('utf8');
          });
        });

        msg.once('end', () => {
          simpleParser(rawEmail, async (err, parsed) => {
            if (err) {
              console.error('❌ Parse error:', err);
              return;
            }

            const emailData = {
              name: parsed.from?.text || '',
              subject: parsed.subject || '',
              detail: parsed.text || '',
              html: parsed.html || ''
            };

            const previewText = parsed.text?.slice(0, 200)?.replace(/\s+/g, ' ') || '[no text]';
            console.log('📩 New Email Received');
            console.log('📨 Subject:', emailData.subject);
            console.log('📝 Preview:', previewText);

            try {
              const tmpDir = path.resolve(__dirname, './tmp');
              if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir);

              const jsonPath = path.join(tmpDir, `${uuidv4()}_email.json`);
              fs.writeFileSync(jsonPath, JSON.stringify(emailData, null, 2));

              const command = `source ${venvActivate} && python ${pythonScriptPath} ${jsonPath}`;

              exec(command, { shell: '/bin/bash' }, (error, stdout, stderr) => {
                console.log('🔧 STDOUT:', stdout);
                console.log('⚠️ STDERR:', stderr);

                if (error) {
                  console.error('❌ EXEC ERROR:', error);
                  return;
                }

                try {
                  const result = JSON.parse(stdout);
                  console.log('✅ Python script result:', result);
                } catch (err) {
                  console.error('❌ JSON PARSE ERROR:', err.message);
                }
              });

              // Optionally log email
              const logPath = path.join(__dirname, 'emails.log');
              fs.appendFileSync(logPath, JSON.stringify(emailData, null, 2) + '\n\n');
              console.log('✅ Email data logged');
            } catch (error) {
              console.error('❌ Email processing error:', error.message);
            }
          });
        });
      });

      nextUid++;
    });
  });
});

imap.once('error', function (err) {
  console.error('❌ IMAP error:', err);
});

imap.once('end', function () {
  console.log('📭 IMAP connection ended');
});

imap.connect();