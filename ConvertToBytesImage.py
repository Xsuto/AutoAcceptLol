import numpy as np
import cv2
import io
import sys

img_name = sys.argv[1]

img = cv2.imread("lockin.png",0)

# encode
is_success, buffer = cv2.imencode("that.png", img)
io_buf = io.BytesIO(buffer)
buffer.tofile("imageasbytes.txt",",")
print(buffer)


# sd = ""

# ds = np.fromstring(sd,np.uint8,sep=",")
# decode_img = cv2.imdecode(ds, -1)
# cv2.imshow("fgasd",decode_img)
# cv2.waitKey()   # True