import socket
from threading import Thread
import re


def main():
    connection = True
    while connection:
        # Create a socket object
        s = socket.socket()

        # Define the port on which you want to connect
        port = 50000

        # connect to the server on local computer
        s.connect(('127.0.0.1', port))
        message = s.recv(1024).decode()
        print(message)
        choice = input('enter your number of choice\r\nenter 1 for sign up\r\nenter 2 for login\r\n')
        is_authenticated = Authentication.authenticate(choice=int(choice), soc=s)
        if is_authenticated:
            connection = Client.main(connection=s)
            

class Client:
    username = None
    connection = None
    joined_group = None
    communication_flag = True

    @classmethod
    def listen_for_messages(cls):
        while cls.communication_flag:
            # print group messages and private messages to appropriate format
            messg = cls.connection.recv(1024).decode()
            event = messg.split(' ')[0]
            if event == 'GM':
                group_name = re.search('<to:(.+?)>', messg).group(1)
                actor_user = re.search('<from:(.+?)>', messg).group(1)
                msg = re.search('<message_body:"(.+?)">', messg).group(1)
                print(f'{actor_user} sent a message to group {group_name}:\r\n{msg}')
            elif event == 'PM':
                actor_user = re.search('<from:(.+?)>', messg).group(1)
                msg = re.search('<message_body:"(.+?)">', messg).group(1)
                print(f'user {actor_user} sent you a private message:\r\n{msg}')
            else:
                print(f'{messg}\r\n')

    @classmethod
    def main(cls, connection):
        # we create a listening thread to be able to receive messages from server while the main
        # thread is busy handling user requests
        cls.connection = connection
        Thread(target=cls.listen_for_messages).start()
        print('use bellow options to interact with the app in all menus\r\n'
              'choose one of the options bellow:\r\n'
              'enter 1 to join a group \r\n'
              'enter 2 to send a message to a group of choice\r\n'
              'enter 3 to get list of current group users\r\n'
              'enter 4 to send a private message to a user\r\n'
              'enter 5 to exit your joined group\r\n'
              'enter 6 to create a group\r\n'
              'enter 7 to exit messenger app\r\n'
              'enter 8 for help')
        while cls.communication_flag:
            # get user's choice and act accordingly
            # we communicate to the server using an especial protocol custom made for this application
            choice = int(input())
            if choice == 1:
                cls.joined_group = input("enter group name:\r\n")
                connection.send(f'Group -Option <user:{cls.username}> -Option <gname:{cls.joined_group}>'.encode())
            elif choice == 2:
                group_name = input("enter group to send message:\r\n")
                msg = input("enter your message: \r\n")
                connection.send(f'GM -Option <to:{group_name}> -Option <message_body:"{msg}">'.encode())
            elif choice == 3:
                if cls.joined_group:
                    connection.send(f'Users -Option <user:{cls.username}> -Option <gname:{cls.joined_group}>'.encode())
                    list_of_users = connection.recv(1024).decode()
                    print(list_of_users)
                else:
                    print('join a group first!')
            elif choice == 4:
                target_user = input('write the username of your target_user: ')
                msg = input('write your message:\r\n')
                connection.send(f'PM -Option <to:{target_user}> -Option <message_body:"{msg}">'.encode())
            elif choice == 5:
                group_to_leave = input('write the group name you want to leave: ')
                connection.send(f'End -Option <gname:{group_to_leave}>'.encode())
            elif choice == 6:
                group_name = input('enter the group name you want to create\r\n'
                                   'notice that the group names are unique\r\n')
                connection.send(f'CG -Option <gname:{group_name}> -Option <user:{cls.username}>'.encode())
            elif choice == 7:
                connection.send(f'EndAll'.encode())
                cls.communication_flag = False
            elif choice == 8:
                print('use bellow options to interact with the app in all menus\r\n'
                      'choose one of the options bellow:\r\n'
                      'enter 1 to join a group \r\n'
                      'enter 2 to send a message to a group of choice\r\n'
                      'enter 3 to get list of current group users\r\n'
                      'enter 4 to send a private message to a user\r\n'
                      'enter 5 to exit your joined group\r\n'
                      'enter 6 to create a group\r\n'
                      'enter 7 to exit messenger app\r\n'
                      'enter 8 for help')

        return False


class Authentication:

    @classmethod
    def sign_up(cls, connection):
        # get username and password and send them to the server
        username = input('choose a username: ')
        password = input('choose a password: ')
        connection.send(f'Make -Option <user:{username}> -Option <pass:{password}>'.encode())
        user_acceptance = connection.recv(1024).decode()
        print(user_acceptance)
        if user_acceptance == 'User Accepted':
            Client.username = username
            return True
        return False

    @classmethod
    def login(cls, connection):
        # try to login to an existing account on the server
        username = input('enter your username: ')
        password = input('enter your password: ')
        connection.send(f'Connect -Option <user:{username}> -Option <pass:{password}>'.encode())
        user_acceptance = connection.recv(1024).decode()
        print(user_acceptance)
        if user_acceptance == 'Connected':
            Client.username = username
            return True
        return False

    @classmethod
    def authenticate(cls, choice, soc):
        # check and run authentication functions based on user choice
        if choice == 1:
            return Authentication.sign_up(soc)
        elif choice == 2:
            return Authentication.login(soc)
        else:
            print('invalid input')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
