from translatorv2 import main as translator_main
from model import main as model_main

translator_main("source.forth", "program.lab")
model_main("program.lab", "input.txt", "out.txt")