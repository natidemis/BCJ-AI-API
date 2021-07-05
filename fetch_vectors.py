import gdown
import tarfile
import os.path

output = 'GoogleNews-vectors-negative300.bin.gz' #name of file
if not os.path.exists(output):
    print("hmm")
    url = 'https://drive.google.com/uc?id=0B7XkCwpI5KDYNlNUTTlSS21pQmM' #sharable drive link
    gdown.download(url, output, quiet=False)

    #Ef við zippum sem tar skrá -- 
    #file = tarfile.open(output)
    #  
    ## extracting file
    #file.extractall('GoogleNews-vectors-negative300.bin')
    #  
    #file.close()
