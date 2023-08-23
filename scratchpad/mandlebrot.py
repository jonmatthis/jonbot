import matplotlib.pyplot as plt
import numpy as np


def mandelbrot(c, max_iter):
    z = c
    for n in range(max_iter):
        if abs(z) > 2:
            return n
        z = z * z + c
    return max_iter


def draw_mandelbrot(xmin, xmax, ymin, ymax, width, height, max_iter):
    r1 = np.linspace(xmin, xmax, width)
    r2 = np.linspace(ymin, ymax, height)
    return (
        r1,
        r2,
        np.array([[mandelbrot(complex(r, i), max_iter) for r in r1] for i in r2]),
    )


def main():
    dpi = 80
    img_width = 800
    img_height = 800
    xmin, xmax, ymin, ymax = -2.0, 1.0, -1.5, 1.5
    width = dpi * img_width
    height = dpi * img_height
    max_iter = 256

    x, y, image = draw_mandelbrot(xmin, xmax, ymin, ymax, width, height, max_iter)
    plt.imshow(image, extent=(xmin, xmax, ymin, ymax))
    plt.show()


if __name__ == "__main__":
    main()
