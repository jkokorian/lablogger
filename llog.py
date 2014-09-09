import argparse


parser = argparse.ArgumentParser(prog="LabLogger",
                                 description="A markdown based logging tool")

subparsers = parser.add_subparsers()

p_generate = subparsers.add_parser("generate",help="generate a sample or multple samples")


p_generate.add_argument("-n","--amount",
                        help="the number of samples to generate",
                        type=int,
                        default=1)
p_generate.add_argument("-g","--generator",
                        help="the name generator to use",
                        choices=["alpha","num"],
                        default="num")





args = parser.parse_args()

print args