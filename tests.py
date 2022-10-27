import unittest
from client import Authentication
from client import Client
import socket


class TestFunctionality(unittest.TestCase):
    def setUp(self):
        s = socket.socket()
        port = 50000

        # connect to the server on local computer
        s.connect(('127.0.0.1', port))
        message = s.recv(1024).decode()
        print(message)
        s.send(f'Make -Option <user:dummy> -Option <pass:dummydummy>'.encode())
        user_acceptance = s.recv(1024).decode()
        print(user_acceptance)
        s.close()

    def test_login(self):
        s = socket.socket()
        port = 50000

        # connect to the server on local computer
        s.connect(('127.0.0.1', port))
        message = s.recv(1024).decode()
        print(message)
        s.send(f'Connect -Option <user:dummy> -Option <pass:dummydummy>'.encode())
        user_acceptance = s.recv(1024).decode()
        assert user_acceptance == 'Connected'
        s.close()

    def test_signUp(self):
        s = socket.socket()
        port = 50000

        # connect to the server on local computer
        s.connect(('127.0.0.1', port))
        message = s.recv(1024).decode()
        print(message)
        s.send(f'Make -Option <user:dumb> -Option <pass:dumb>'.encode())
        user_acceptance = s.recv(1024).decode()
        assert user_acceptance == 'User Accepted'
        s.close()

    def test_login_fail(self):
        s = socket.socket()
        port = 50000

        # connect to the server on local computer
        s.connect(('127.0.0.1', port))
        message = s.recv(1024).decode()
        print(message)
        s.send(f'Connect -Option <user:dummylkjl> -Option <pass:dummydummyjjj>'.encode())
        user_acceptance = s.recv(1024).decode().split(' ')[0]
        assert user_acceptance == 'ERROR'
        s.close()

    def test_signUp_fail(self):
        s = socket.socket()
        port = 50000
        username = 'ksjdf;lknkjnkjsjfjsldjflskjdfl;kjsflkj;lkj;ldfkjslkdjflksjdf;ljs;liiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiieteetlrkjtlkejlrktjlekjrltkjdfkj;sldfj;lskjdf;lsjdflkjs;ldfj;slkdjf;lsjdf;lsjdf;lkjsdl;fkjs;lkdjf;ljlhhkjn,nj;ditojdr;ltkj;aiajoosfasdf;kajsd;flkjlsdjf;lsakjdfl;sjdf;lks;dlknkdgkjfdoijgkdfjg;ladkjgfgl;ajdlfkja;lkdjf;df;ajf;odij'
        # connect to the server on local computer
        s.connect(('127.0.0.1', port))
        message = s.recv(1024).decode()
        print(message)
        s.send(f'Make -Option <user:{username}> -Option <pass:dummydummy>'.encode())
        user_acceptance = s.recv(1024).decode()
        assert user_acceptance == 'User Not Accepted'
        s.close()


if __name__ == '__main__':
    unittest.main()
