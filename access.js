// Logs
// ssh -i your-key.pem ec2-user@your-ec2-ip
// ssh -i email-automation-keys.pem ec2-user@13.43.87.188
// cat ~/email-watcher/emails.log
// tail -f ~/email-watcher/emails.log

// Starting the IMAP server
// pm2 start emailAutomation.js --name email-watcher
// start on reboot: pm2 startup
// save processes: pm2 save
// view logs live: pm2 logs email-watcher
// list all processes: pm2 list
// stop or restart: pm2 stop email-watcher
//                  pm2 restart email-watcher