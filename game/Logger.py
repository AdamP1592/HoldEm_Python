class Logger():
    def __init__(self, fp = "/logs", file_name ="log.log"):
        self.folder_path = fp
        self.file_name = file_name
        self.full_filepath = "." + fp + file_name #generates relative folder path
        self.generate_path()
    
    def generate_path(self):
        import os
        try:
            os.mkdir(self.folder_path)
        except FileExistsError:
            print(f"Folder '{self.folder_path}' already exists")

    #creates a file if it doesn't exist, clears it if it does exist
    def clear_file(self):
        open(self.full_filepath, 'w+').close()
    
    def log(self, log_str):
        with open(self.full_filepath, "a") as f:
            f.write(log_str + '\n')