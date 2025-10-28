class User:
    def __init__(self, username: str, pontuation: int = 0):
        self.username = username
        self.pontuation = pontuation

    def get_info(self):
        return f"Username: {self.username}, Pontuação: {self.pontuation}"
    
    