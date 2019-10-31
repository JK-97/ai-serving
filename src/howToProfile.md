
1. python -m cProfile -o run.profile run.py 

2. Then the output file can be read as follows:

```python
import pstats

p = pstats.Stats('run.profile')
p.sort_stats('cumtime').print_stats()
# which is sorted by cumulative time
```

3. If graph visualization is needed:

```bash
apt install graphviz
pip install gprof2dot
gprof2dot -f pstats run.profile | dot -Tsvg -o run.svg
```