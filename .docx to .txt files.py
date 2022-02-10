#pip3 install docx2txt


import os
import docx2txt

'''
The directory you set is the path to the folder with the files you want to change from .docx files to .txt files
Make sure the path is in quotations, as seen below
'''
directory= "/Users/Desktop/folder/subfolder/folder containing .docx files"
for docfilename in os.listdir(directory):
    if docfilename.endswith(".docx"):
        FullFileCall=(os.path.basename(docfilename))
        filename=os.path.splitext(FullFileCall)[0]
        txtfile = docx2txt.process(os.path.join(directory, docfilename))
        '''
        This open statement is which folder you want to write all your text files to.
        The file path you place here (in quotations) will write your files to that path
        At the end of the file path, ensure there is a forward slash or backslash to write the files INTO that folder
        Windows users will use a back slash
        Unix systems (Linux, OS X (apple users), and Android will all use a forward slash
        '''
        with open("/Users/Desktop/Folder/subfolder/folder the files go into/" + filename +".txt", 'x') as NewTxtFile:
            NewTxtFile.write(txtfile)
            NewTxtFile.close()

    else:
        exit()





