-- CP Python snippets. Trigger with `<prefix><Tab>` in insert mode.
-- Edit this file and restart nvim to pick up changes (no rebuild needed).
local ls = require("luasnip")
local s = ls.snippet
local i = ls.insert_node
local fmt = require("luasnip.extras.fmt").fmt

return {
  -- I/O ----------------------------------------------------------------
  s("ii",  fmt("{} = int(input())",                      { i(1, "n") })),
  s("if",  fmt("{} = float(input())",                    { i(1, "f") })),
  s("is",  fmt("{} = input()",                           { i(1, "s") })),
  s("il",  fmt("{} = list(map(int, input().split()))",   { i(1, "a") })),
  s("im",  fmt("{}, {} = map(int, input().split())",     { i(1, "n"), i(2, "m") })),
  s("ig",  fmt("{} = [list(map(int, input().split())) for _ in range({})]",
               { i(1, "g"), i(2, "n") })),
  -- T if Condition else False --------------------------------------------------------------
  s("pif",  fmt("print(\"Yes\" if {} else \"No\")",      { i(1, "") })),

  -- Loops --------------------------------------------------------------
  s("fr",  fmt("for {} in range({}):\n    {}",           { i(1, "i"), i(2, "n"), i(3) })),
  s("lc",  fmt("[{} for {} in range({})]",               { i(1), i(2, "_"), i(3, "n")})),

  -- Conditions --------------------------------------------------------------
  s("f",  fmt("\"{}\" if ({}) else \"{}\"",              { i(1, "Yes"), i(2), i(3, "No")})),

  -- Grid ---------------------------------------------------------------
  s("2d",  fmt("{} = list(map(int, input().split()))",      { i(1, "") })),

  -- Boilerplate --------------------------------------------------------
  s("main", fmt([[
import sys
input = sys.stdin.readline

def solve():
    {}

solve()
]], { i(1) })),
}
