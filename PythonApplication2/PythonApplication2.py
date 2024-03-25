import os
from datetime import datetime
from threading import Thread
from PIL import Image
import hashlib

class GitBackgroundThread:
    def __init__(self, gitInstance, intervalMilliseconds):
        self.gitInstance = gitInstance
        self.intervalMilliseconds = intervalMilliseconds
        self.isRunning = False
        self.backgroundThread = None

    def start(self):
        if self.isRunning:
            return
        self.isRunning = True
        self.backgroundThread = Thread(target=self.backgroundTask)
        self.backgroundThread.daemon = True
        self.backgroundThread.start()

    def stop(self):
        self.isRunning = False

    def backgroundTask(self):
        while self.isRunning:
            self.gitInstance.pasivestatus()
            import time
            time.sleep(self.intervalMilliseconds / 1000.0)

class Git:
    def __init__(self):
        self.rootDirectory = self.initializeRootDirectory()
        solutionDirectory = os.path.dirname(os.path.dirname(self.rootDirectory))
        self.snapshotFilePath = os.path.join(solutionDirectory, "snapshot.txt")

    def initializeRootDirectory(self):
        rootDirectory = os.path.dirname(os.path.abspath(__file__))
        while not any(file.endswith(".csproj") for file in os.listdir(rootDirectory)):
            rootDirectory = os.path.dirname(rootDirectory)
        rootDirectory = os.path.join(rootDirectory, "test")
        return rootDirectory

    def info(self, input):
        parts = input.split('<')
        if parts[1].endswith('>'):
            parts[1] = parts[1][:-1]
        fileName = parts[1]
        fullPath = os.path.join(self.rootDirectory, fileName)

        if os.path.exists(fullPath):
            crtime = datetime.fromtimestamp(os.path.getctime(fullPath))
            uptime = datetime.fromtimestamp(os.path.getmtime(fullPath))
            print(f"Name: {parts[1]}")
            print(f"Created on: {crtime}")
            print(f"Updated on: {uptime}")
        else:
            print(f"File {fileName} does not exist")
            return

        ext = fileName.split(".")
        if ext[1] == "txt":
            with open(fullPath, 'r') as file:
                lines = file.readlines()
                lcount = len(lines)
                print(f"Lines: {lcount}")
                words = ' '.join(lines).split()
                wcount = len(words)
                print(f"Words: {wcount}")
                ccount = sum(len(word) for word in words)
                print(f"Characters: {ccount}")
        elif ext[1] in ["jpg", "jpeg", "png", "svg"]:
            with Image.open(fullPath) as img:
                width, height = img.size
                print(f"Image size: {width}x{height}")
        elif ext[1] in ["cs", "java", "py"]:
            with open(fullPath, 'r') as file:
                lines = file.readlines()
                lcount = len(lines)
                print(f"Lines: {lcount}")
                clcount = sum(1 for line in lines if "class" in line)
                print(f"Classes in code: {clcount}")

    def commit(self):
        print(f"[SNAPSHOT CREATED AT {datetime.now()}]")
        files = [os.path.join(root, file) for root, _, files in os.walk(self.rootDirectory) for file in files]
        currentSnapshot = {file: self.calculateFileHash(file) for file in files}
        self.saveSnapshot(currentSnapshot)

    def loadPreviousSnapshot(self):
        previousSnapshot = {}
        if os.path.exists(self.snapshotFilePath):
            with open(self.snapshotFilePath, 'r') as file:
                for line in file:
                    parts = line.split('|')
                    if len(parts) == 2:
                        previousSnapshot[parts[0]] = parts[1]
        return previousSnapshot

    def saveSnapshot(self, currentSnapshot):
        with open(self.snapshotFilePath, 'w') as file:
            for key, value in currentSnapshot.items():
                file.write(f"{key}|{value}\n")

    def calculateFileHash(self, filePath):
        with open(filePath, 'rb') as file:
            md5 = hashlib.md5()
            md5.update(file.read())
            return md5.hexdigest()

    def status(self):
        previousSnapshot = self.loadPreviousSnapshot()
        currentSnapshot = {file: self.calculateFileHash(file) for file in os.listdir(self.rootDirectory)}

        print("State of files since last snapshot:")
        for file, currentHash in currentSnapshot.items():
            if file in previousSnapshot:
                previousHash = previousSnapshot[file]
                if currentHash != previousHash:
                    print(f"{os.path.basename(file)} - Edited")
                else:
                    print(f"{os.path.basename(file)} - No changes")
            else:
                print(f"{os.path.basename(file)} - Added")

        for file in previousSnapshot:
            if file not in currentSnapshot:
                print(f"{os.path.basename(file)} - Deleted")

    def pasivestatus(self):
        previousSnapshot = self.loadPreviousSnapshot()

        files = [os.path.join(root, file) for root, _, files in os.walk(self.rootDirectory) for file in files]
        currentSnapshot = {file: self.calculateFileHash(file) for file in files}

        for file, currentHash in currentSnapshot.items():
            if file in previousSnapshot:
                previousHash = previousSnapshot[file]
                if currentHash != previousHash:
                    print(f"{os.path.basename(file)} - Edited")
            else:
                print(f"{os.path.basename(file)} - Added")

        for file in previousSnapshot:
            if file not in currentSnapshot:
                print(f"{os.path.basename(file)} - Deleted")

# Example Usage:
if __name__ == "__main__":
    git_instance = Git()
    background_thread = GitBackgroundThread(git_instance, 1000)  # 1000 milliseconds
    background_thread.start()
