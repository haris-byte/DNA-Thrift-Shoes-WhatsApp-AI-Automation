# Day 6-ready manual test matrix

| ID | Input | Expected result |
|---|---|---|
| T01 | `Air Jordan 1 size 10` | Exact match, Rs. 18,500, purchase intent state |
| T02 | `Air Force 1 size 10` | Exact Air Force match, Rs. 9,450 |
| T03 | `Air Jordan 1 size 8` | Partial match with nearby sizes |
| T04 | `Nike Unknown Runner size 10` | No exact model, Nike alternatives |
| T05 | `Nike shoes?` | Ask model + US size |
| T06 | Repeat `Nike shoes?` twice after first question | Human/category fallback |
| T07 | `Air Force 1` then `US 10` | Partial details merge correctly |
| T08 | Duplicate message ID | Same cached response; state does not advance twice |
| P01 | Clear full shoe + readable US tag | VLM + OCR + inventory response |
| P02 | Clear shoe, hidden/unreadable tag | Ask for US size |
| P03 | Clear tag with EU 44 only | Ask to confirm US size |
| P04 | Unknown/uncertain shoe | Ask for exact model or clearer image |
| P05 | Corrupted file | Structured 415 error |
| P06 | Private URL such as localhost | Blocked download |
| W01 | Valid Meta verification token | Challenge returned |
| W02 | Invalid Meta verification token | 403 |
| W03 | Valid Meta text webhook | Conversation reply sent |
| W04 | Valid Meta image webhook | Media downloaded, analyzed, reply sent |
| V01 | Blank text | Structured 422 error |
| V02 | Unknown webhook field | Structured 422 error |
| V03 | Unsupported message type | Structured 422 error |
