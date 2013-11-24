class PlayerWrapper(object):

    def __init__(self):
        super(PlayerWrapper, self).__init__()

    @property
    def position(self):
        raise NotImplementedError

    @property
    def stopped(self):
        raise NotImplementedError

    def play(self, file_path):
        raise NotImplementedError

    def toggle_pause(self):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        #self.close()
        return False
