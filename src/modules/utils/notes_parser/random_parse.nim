import nimpy
import nre
import strutils
import random


proc random_parser(text: string): string {.exportpy.} =
  var str = text

  for item in nre.findIter(text, re"({([^{}]+)})"):
    let captured = item.captures[1]
    if not captured.contains("|"):
      continue

    let random_item = sample(captured.split("|"))
    str = str.replace(item.captures[0], random_item)

  return str

