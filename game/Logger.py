class Logger():
    def __init__(self, folder_path = "/logs/", file_name ="log.log", reset=False):
        self.folder_path = "." + folder_path
        self.file_name = file_name
        self.full_filepath = self.folder_path + file_name #generates relative folder path
        self.generate_path()
        if reset:
            self.clear_file()
    
    def generate_path(self):
        import os
        try:
            os.mkdir(self.folder_path)
        except FileExistsError:
            print(f"Folder '{self.folder_path}' already exists")

    #creates a file if it doesn't exist, clears it if it does exist
    def clear_file(self):
        open(self.full_filepath, 'w+').close()
    
    def log(self, log_str, end = "\n"):
        with open(self.full_filepath, "a", encoding="utf-8") as f:
            f.write(log_str + end)