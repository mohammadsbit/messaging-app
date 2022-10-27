import socket as soc
import re
import bcrypt
from threading import Thread
import mysql.connector as db
from mysql.connector import ProgrammingError
from decouple import config


def main():
    print('initializations are done')
    # create a server instance and listen for incoming connections in a while loop when
    # new connections arrive the program serves them in seperated threads this way
    # we can handle new connections and previous connections the same time
    server = MyTcpServer('127.0.0.1', 50000)
    while True:
        connection, addr = server.wait_accept()
        Thread(target=server.handle_request, args=[connection, addr]).start()


class MyTcpServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
        self.server.bind((self.ip, self.port))
        self.server.listen(5)

    def wait_accept(self):
        connection, addr = self.server.accept()
        return connection, addr

    def handle_request(self, connection, addr):
        print('Got connection from', addr)
        # send a thank you message to the client. encoding to send byte type.
        connection.send('Thank you for connecting'.encode())
        messg = connection.recv(1024).decode()
        messg_segments = messg.split(' ')
        option = messg_segments[0]
        communication_flag = True
        handling_username = None
        # this is where authentication takes place notice that the program uses regular expressions to
        # obtain necessary data from the program protocol
        if option == 'Make':
            username = re.search('<user:(.+?)>', messg).group(1)
            password = re.search('<pass:(.+?)>', messg).group(1)
            if not Authentication.sign_up(username=username, password=password, connection=connection):
                communication_flag = False
            handling_username = username
        elif option == 'Connect':
            username = re.search('<user:(.+?)>', messg).group(1)
            password = re.search('<pass:(.+?)>', messg).group(1)
            if not Authentication.log_in(username=username, password=password, connection=connection):
                communication_flag = False
            handling_username = username
        else:
            connection.send('Error -Option <reason:Protocol Violation>'.encode())
            communication_flag = False

        # user can enter bellow while loop if they have passed the authentication phase
        while communication_flag:
            # call functions to perform the desired functionality requested by the user
            messg = connection.recv(1024).decode()
            choice = messg.split(' ')[0]
            if choice == 'Group':
                username = re.search('<user:(.+?)>', messg).group(1)
                if 'gname' in messg:
                    group_name = re.search('<gname:(.+?)>', messg).group(1)
                    Authentication.add_user_to_group(group_name=group_name, username=username)
                    # messg = connection.recv(1024).decode()
            elif choice == 'Users':
                username = re.search('<user:(.+?)>', messg).group(1)
                group_name = re.search('<gname:(.+?)>', messg).group(1)
                Authentication.send_list_of_group_users(group_name, username)
            elif choice == 'GM':
                group_name = re.search('<to:(.+?)>', messg).group(1)
                msg = re.search('<message_body:"(.+?)">', messg).group(1)
                Authentication.send_group_message(msg=msg, group_name=group_name, username=handling_username)
            elif choice == 'PM':
                target_user = re.search('<to:(.+?)>', messg).group(1)
                msg = re.search('<message_body:"(.+?)">', messg).group(1)
                Authentication.send_private_message(msg=msg, target_username=target_user, sender_username=handling_username)
            elif choice == 'CG':
                username = re.search('<user:(.+?)>', messg).group(1)
                group_name = re.search('<gname:(.+?)>', messg).group(1)
                Authentication.create_group(group_name=group_name, username=username)
            elif choice == 'End':
                group_name = re.search('<gname:(.+?)>', messg).group(1)
                Authentication.remove_user_from_group(username=handling_username, group_name=group_name)
            elif choice == 'EndAll':
                communication_flag = False
                Authentication.purge_user(username=handling_username)
            else:
                connection.send('Error -Option <reason:Protocol Violation>')
                communication_flag = False

            print(messg)

        # Close the connection with the client
        connection.send('Good Bye'.encode())
        print(f'{handling_username} exited')
        connection.close()


class User:
    # user class to hold user data
    def __init__(self, username, connection):
        self.username = username
        self.groups = set()
        self.connection = connection

    def add_group(self, group_name):
        self.groups.add(group_name)


class Authentication:
    """the program uses dictionaries to store current logged in users and the groups they have joined in the User model
    also it stores group data and each groups users here"""
    users = {}
    groups = {}

    @classmethod
    def hash_password(cls, password):
        # this function uses the bcrypt module to hash the passwords with salt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    @classmethod
    def check_password(cls, password, hashed_password):
        # this function is used to validate a hashed_password to match the entered password
        return bcrypt.checkpw(password=password.encode(), hashed_password=hashed_password.encode())

    @classmethod
    def sign_up(cls, username, password, connection):
        # uses DBMS class to insert user info into User table then stores username and connection
        # to users dictionary in order to be accessible in the program and throws an exception
        # in case something goes wrong
        try:
            DBMS.insert_user(username=username, hashed_password=cls.hash_password(password))
            cls.users[username] = User(username=username, connection=connection)
            connection.send('User Accepted'.encode())
            print(f'{username} signed up successfully')
            return True
        except Exception as ex:
            connection.send(f'User Not Accepted -Option <reason:{ex}>'.encode())
            return False

    @classmethod
    def log_in(cls, username, password, connection):
        # retrieves a user's hashed password from the db to be compared to the password entered by
        # the current user then if everything went ok grants access to the user
        retrieved_password = DBMS.retrieve_password(username=username)
        try:
            result = cls.check_password(password=password, hashed_password=retrieved_password)
            if result and retrieved_password != "user was not found":
                cls.users[username] = User(username=username, connection=connection)
                connection.send('Connected'.encode())
                print(f'{username} logged in successfully')
            else:
                connection.send('ERROR -Option <reason:user name or password is wrong>'.encode())
            return result
        except Exception as ex:
            connection.send('ERROR -Option <reason:username or password is wrong>'.encode())
            return False

    @classmethod
    def sign_out(cls):
        pass

    @classmethod
    def add_user_to_group(cls, group_name, username):
        # if a group exists the code adds the user to the specified group
        # and then sends a message to all chat participants that the user
        # entered the chat
        if group_name in cls.groups:
            for user in cls.groups[group_name]:
                cls.users[user].connection.send(f'{username} joined the chat room.'.encode())
            cls.groups[group_name].append(username)
            cls.users[username].add_group(group_name=group_name)
            cls.users[username].connection.send(f'Hi {username}, welcome to the chat room.'.encode())
            print(f'user {username} was added to {group_name}')
        else:
            print('group not found')

    @classmethod
    def send_list_of_group_users(cls, group_name, username):
        # sends the list of all chat participants
        if group_name in cls.groups and username in cls.groups[group_name]:
            users_list = cls.groups[group_name]
            msg = ""
            for user in users_list:
                msg += f"|<{user}>"
            final_msg = "USERS LIST:\r\n" + msg[1:]
            cls.users[username].connection.send(final_msg.encode())
            print(f'{group_name} users list was sent to {username}')

    @classmethod
    def send_group_message(cls, msg, group_name, username):
        # sends a group message to all group_users that are in the named chat
        if group_name in cls.groups and username in cls.groups[group_name]:
            target_users = cls.groups[group_name]
            for user_name in target_users:
                cls.users[user_name].connection.send(f'GM -Option <from:{username}> -Option <to:{group_name}> -Option <message_body:"{msg}">'.encode())
            print(f'user {username} sent a group message to {group_name}')

    @classmethod
    def send_private_message(cls, msg, target_username, sender_username):
        # sends a pm to the requested user
        if target_username in cls.users:
            cls.users[target_username].connection.send(f'PM -Option <from:{sender_username}> -Option <to:{target_username}> -Option <message_body:"{msg}">'.encode())
            print(f'user {sender_username} sent a pm to {target_username}')

    @classmethod
    def remove_user_from_group(cls, username, group_name):
        if username in cls.users:
            cls.groups[group_name].remove(username)
            print(f'user {username} was removed from {group_name}')

    @classmethod
    def purge_user(cls, username):
        cls.users.pop(username)
        for group in cls.groups:
            for item in group:
                if item == username:
                    item.delete()
        print(f'all user activity of {username} was purged from the server')

    @classmethod
    def create_group(cls, group_name, username):
        # creates a group with the name specified
        cls.groups[group_name] = []
        cls.groups[group_name].append(username)
        cls.users[username].add_group(group_name=group_name)
        print(f'{username} created a group named {group_name}')
        cls.users[username].connection.send(f'user {username} created a group named {group_name}'.encode())


class DBMSMetaclass(type):
    """this metaclass is used to run custom code before the initialization of the dbms class
    first we connect to database using credentials specified in .env file then we try to create
    User table and if it already exists we do nothing"""
    def __new__(mcs, name, bases, attrs):
        connection = db.connect(host=config('DB_HOST'),
                                database=config('DB_NAME'),
                                user=config('DB_USER'),
                                password=config('DB_PASS'))
        cursor = connection.cursor()
        try:
            cursor.execute("CREATE TABLE User (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) not null, password VARCHAR(356) not null)")
        except ProgrammingError as ex:
            pass
        attrs['connection'] = connection
        attrs['cursor'] = cursor
        return type.__new__(mcs, name, bases, attrs)


class DBMS(metaclass=DBMSMetaclass):

    @classmethod
    def insert_user(cls, username, hashed_password):
        # adds a user to the db and we call commit to perform the actual write oporation
        if cls.connection.is_connected():
            cls.cursor.execute(f'INSERT INTO User (username, password) VALUES(%s, %s)', (username, hashed_password.decode()))
            cls.connection.commit()

    @classmethod
    def retrieve_password(cls, username):
        # we try to get the user's password if user doesn't exist we return a message that will be
        # checked and avoids logging in the user
        if cls.connection.is_connected():
            cls.cursor.execute(f'SELECT password FROM User WHERE username = %s', (username,))
            try:
                password = cls.cursor.fetchone()[0]
                return password
            except Exception as ex:
                return "user was not found"


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
