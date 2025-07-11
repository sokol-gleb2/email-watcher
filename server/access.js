// To ssh in:
// ssh -i email-automation-keys.pem ec2-user@35.177.161.224

// To run the docker image:
// docker run -it email_automation
// Then start sending emails to glebsokolovskyi@gmail.com

// Clear all the junk:
// docker system prune -a --volumes

// Rebuild docker image: (<-- you shouldn't need to run this unless you change the Dockerfile or package.json or requirements.txt)
// docker build -t email_automation .

// If node process gets stuck, close the terminal window, open a new one, ssh in again, and run:
    // 1. Check which processes are running
        // ps aux | grep node
        // Output example: root      
            // 6324  0.3  6.8 11595704 67084 ?      Ssl+ 20:55   0:00 node emailAutomation.js

    // 2. Kill a process
        // sudo kill -9 6324






// These logs are for me. don't mind them.
// ssh -i email-automation-keys.pem ec2-user@35.177.161.224
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