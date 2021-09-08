import sys, threading, socket, os, struct, time

def print_to_stderr(*a): 
  
    # Here a is the array holding the objects 
    # passed as the argument of the function 
    print(*a, file = sys.stderr) 

#Create receiveMessages Class
################################################################################
class receiveMess(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock

    def receiveMessage(self):
        while True:
            try:
                #Listen for message
                message = self.sock.recv(1024)
                if message:
                    #Print received
                    print(message.decode())
                else:
                    break
            except:
                continue
        self.sock.shutdown(socket.SHUT_WR)
        self.sock.close()
        os._exit(0)

    def run(self):
        self.receiveMessage()

#Create sendMessages Class
################################################################################
class sendMess(threading.Thread):
        #Create threading object
    def __init__(self, sock, filePort):
        threading.Thread.__init__(self)
        self.sock = sock
        self.filePort = filePort

    def talk(self):
        message = sys.stdin.readline().rstrip('\n')
        try:
            self.sock.send(message.encode())
        except:
            return

    def fileRequest(self):
        fileName = sys.stdin.readline().rstrip('\n')
        try:
            fileSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            fileSock.connect(('localhost', self.filePort))
        except Exception as e:
            print(e)
        try:
            reqFile = fileRequest(fileSock, fileName)
            reqFile.start()
        except Exception as e:
            print(e)

    def userInterface(self):
        while True:
            print('Enter an option (\'m\', \'f\', \'x\'):')
            print(' (M)essage (send)')
            print(' (F)ile (request)')
            print('e(X)it')
            message = sys.stdin.readline().rstrip('\n')
            if message in 'mM':
                self.talk()
            elif message in 'fF':
                self.fileRequest()
            elif message in 'xX':
                os._exit(0)

    def run(self):
        self.userInterface()

#Create fileRequest Class
################################################################################
class fileRequest(threading.Thread):
    def __init__(self, sock, fileName):
        threading.Thread.__init__(self)
        self.sock = sock
        self.file = fileName

    def receiveFile(self, fileName):
        file = open(fileName, 'wb')
        while True:
            fileBytes = self.sock.recv(1024)
            if fileBytes:
                file.write(fileBytes)
            else:
                break
        file.close()
        self.sock.close()
        sys.exit()

    def requestFile(self):
        try:
            self.sock.send(self.file.encode())
        except Exception as e:
            print(e)
            
        try:
            fileBytes = self.sock.recv(4)
            if fileBytes:
                fileSize = struct.unpack('!L', fileBytes[:4])[0]
                if fileSize:
                    self.receiveFile(self.file)
                else:
                    self.sock.close()
                    sys.exit()
        except Exception as e:
            print(e)

    def run(self):
        self.requestFile()

#Create fileSend Class
################################################################################
class findFile(threading.Thread):
    def __init__(self, sock, fileName):
        threading.Thread.__init__(self)
        self.sock = sock
        self.fileName = fileName

    def fileSearch(self):

        try:
            file_stat = os.stat(self.fileName)
            if file_stat.st_size:
                file = open(self.fileName, 'rb')
                self.fileSend(file_stat.st_size, file)
            else:
                self.noFile()
        except OSError:
            self.noFile()

        except Exception as e:
            print(e)
        self.sock.close()
        sys.exit()

    def fileSend(self, fileSize, file):
        fileSizeBytes = struct.pack('!L', fileSize)
        try:
            self.sock.send(fileSizeBytes)
            while True:
                fileBytes = file.read(1024)
                if fileBytes:
                    self.sock.send(fileBytes)
                else:
                    break
        except Exception as e:
            print(e)
        file.close()

    def noFile(self):
        noBytes = struct.pack('!L', 0)
        self.sock.send(noBytes)
        self.sock.close()
        sys.exit()

    def run(self):
        self.fileSearch()
#Startup Initial Server
################################################################################
def runServer(listening_port):
    servSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servSock.bind(('',int(listening_port)))
    servSock.listen(5)

    while True:
        #Connect to Client
        connectedSock, addr = servSock.accept()
        message = connectedSock.recv(1024).decode()
        try:
            #Receive fileServer port if first connection
            filePort = int(message)
            #Start Messaging Thread
            listeningThread = receiveMess(connectedSock)
            sendingThread   = sendMess(connectedSock, filePort)

            listeningThread.start()
            sendingThread.start()

        except:
            searchFile = findFile(connectedSock, message)
            searchFile.start()
            

#Startup Client
################################################################################
def runClient(listening_port, connect_port, connect_addr):
    #Create socket for messages
    messageSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    messageSock.connect((connect_addr, int(connect_port)))
    #Connect message socket
    messageSock.send(listening_port.encode())
    #Send and Receive Messages to and From Main Server

    listeningThread = receiveMess(messageSock)
    sendingThread   = sendMess(messageSock, int(connect_port))

    listeningThread.start()
    sendingThread.start()

#Command Line Handling
################################################################################

if __name__ == "__main__":

    argc = len(sys.argv)

    if argc < 3:
        sys.exit()
    elif argc == 3:
        if sys.argv[1] != '-l':
            sys.exit()
        else:
            listening_port = sys.argv[2]
            runServer(listening_port)
    elif argc > 3 and argc < 8:
        if sys.argv[1] != '-l':
            sys.exit()
        else:
            listening_port = sys.argv[2]
        try:
            if sys.argv[3] == '-p':
                connect_port = sys.argv[4]
        except:
            sys.exit()
        try:
            if sys.argv[5] == '-s':
                connect_addr = sys.argv[6]
        except:
            connect_addr = 'localhost'
        runClient(listening_port, connect_port, connect_addr)
        runServer(listening_port)
        
