require('dotenv').config();
const Imap = require('imap');
const { simpleParser } = require('mailparser');
const axios = require('axios');

const imap = new Imap({
    user: process.env.EMAIL_USER,
    password: process.env.EMAIL_PASS,
    host: process.env.IMAP_HOST,
    port: 993,
    tls: true
});

function openInbox(cb) {
    imap.openBox('INBOX', false, cb);
}

imap.once('ready', function () {
    openInbox(function (err, box) {
        if (err) {
            console.error('❌ Failed to open inbox:', err);
            return;
        }

        console.log('✅ IMAP connected. Watching for new emails...');

        imap.on('mail', function () {
            imap.search(['UNSEEN'], (err, results) => {
                if (err || !results || results.length === 0) return;

                const fetch = imap.fetch(results, { bodies: '', struct: true });

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

                            console.log('📩 New email:', emailData.subject);

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

                                console.log('✅ Email forwarded to backend');
                            } catch (error) {
                                console.error('❌ Failed to send to backend:', error.message);
                            }
                        });
                    });
                });
            });
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
