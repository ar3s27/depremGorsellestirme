import js2py

js = 'function square(x){return x * x}'
py = js2py.eval_js(js)
print(py(3))