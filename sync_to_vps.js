const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  console.log('Sincronizando atualização definitiva para a VPS...');
  conn.sftp((err, sftp) => {
    if (err) throw err;
    
    const localIndex = '/home/skywork/workspace/borges_os/frontend/index.html';
    const remotePath = '/root/borges_os/frontend/index.html';
    
    sftp.fastPut(localIndex, remotePath, (putErr) => {
      if (putErr) throw putErr;
      console.log('index.html sincronizado.');
      
      const cmd = `
        docker exec borges_os-api-1 cp /app/frontend/index.html /app/public/index.html && \
        docker restart borges_os-api-1
      `;
      
      conn.exec(cmd, (execErr, stream) => {
        if (execErr) throw execErr;
        stream.on('close', () => {
          console.log('VPS atualizada. Logout e Dashboard corrigidos.');
          conn.end();
        });
      });
    });
  });
}).connect({
  host: '31.97.247.28',
  port: 22,
  username: 'root',
  password: 'Borges35133@'
});
