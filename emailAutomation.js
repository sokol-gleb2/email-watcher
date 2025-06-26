require('dotenv').config();
const Imap = require('imap');
const { simpleParser } = require('mailparser');
const axios = require('axios');

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

        // Save the UID of the next email that will arrive
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
                            from: parsed.from?.text,
                            subject: parsed.subject,
                            text: parsed.text,
                            html: parsed.html
                        };

                        
                        const previewText = parsed.text?.slice(0, 200)?.replace(/\s+/g, ' ') || '[no text]';
                        console.log('📩 New Email Received');
                        console.log('📨 Subject:', parsed.subject || '[no subject]');
                        console.log('📝 Preview:', previewText);


                        try {
                            const fs = require('fs');
                            const path = require('path');

                            const logPath = path.join(__dirname, 'emails.log');

                            fs.appendFile(logPath, JSON.stringify(emailData, null, 2) + '\n\n', err => {
                                if (err) {
                                    console.error('❌ Failed to write to file:', err);
                                } else {
                                    console.log('✅ Email data saved to emails.log');
                                }
                            });
                        } catch (error) {
                            console.error('❌ Error handling email:', error.message);
                        }
                    });
                });
            });

            // Increment UID so we don’t re-process the same message
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