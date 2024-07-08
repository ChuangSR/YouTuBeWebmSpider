class Util:
    @staticmethod
    def replace_name(input_str):
        char_list = ['*', '|', ':', '?', '/', '<', '>', '"', '\\']
        for i in char_list:
            if i in input_str:
                input_str = input_str.replace(i, "_")
        return input_str
    @staticmethod
    def get_path(path, name):
        if path[-1] == "/":
            return path + name
        else:
            return path + "/" + name