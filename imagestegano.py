from PIL import Image
import numpy as np
from pathlib import Path
import hashlib
import imageshuffle
import argparse


class ImageStegano(object):
	"""docstring for ImageStegano"""
	def __init__(self):
		super(ImageStegano, self).__init__()
		
	# --- Image Encryption Function ---

	def encryptImage(self,image,passcode):
	    img_arr = np.asarray(image)
	    key = int(hashlib.sha1(passcode.encode('utf-8')).hexdigest(), 16) % (10 ** 8)
	    shuffler = imageshuffle.Rand(key)
	    enc_arr = shuffler.enc(img_arr)
	    enc_img = Image.fromarray(enc_arr)
	    return enc_img

	# --- Image Decryption Function ---

	def decryptImage(self,image,passcode):
	    img_arr = np.asarray(image)
	    key = int(hashlib.sha1(passcode.encode('utf-8')).hexdigest(), 16) % (10 ** 8)
	    shuffler = imageshuffle.Rand(key)
	    dec_arr = shuffler.dec(img_arr)
	    dec_img = Image.fromarray(dec_arr)
	    return dec_img


	# --- Slower Merge and Unmerge Sub-Functions ---

	# def __merge_rgb(self,rgb1,rgb2):
	# 	r1, g1, b1 = rgb1
	# 	r2, g2, b2 = rgb2
	# 	rgb = ((r1-(r1%16)) + r2//16,
	#            (g1-(g1%16)) + g2//16,
	#            (b1-(b1%16)) + b2//16)
	# 	return rgb

	# def merge(self,img1,img2):
	# 	pixel_map1 = img1.load()
	# 	pixel_map2 = img2.load()

	# 	new_image = Image.new(img1.mode, img1.size)
	# 	pixels_new = new_image.load()

	# 	for i in range(img1.size[0]):
	# 		for j in range(img1.size[1]):
	# 			rgb1 = pixel_map1[i, j]
	# 			rgb2 = (0, 0, 0)
	# 			if i < img2.size[0] and j < img2.size[1]:
	# 				rgb2 = pixel_map2[i, j]
	# 			rgb = self.__merge_rgb(rgb1, rgb2)
	# 			pixels_new[i,j] = rgb
		
	# 	return new_image


	# def unmerge(self,img):
	# 	pixel_map = img.load()

	# 	new_image = Image.new(img.mode, img.size)
	# 	pixels_new = new_image.load()

	# 	original_size = img.size

	# 	for i in range(img.size[0]):
	# 		for j in range(img.size[1]):
	# 			r, g, b = pixel_map[i, j]
	# 			pixels_new[i, j] = ((r%16)*16,(g%16)*16,(b%16)*16)
	# 			if pixels_new[i, j] != (0, 0, 0):
	# 				original_size = (i + 1, j + 1)
		
	# 	new_image = new_image.crop((0, 0, original_size[0], original_size[1]))
	# 	return new_image


	# --- Faster Merge and Unmerge Sub-Functions using Numpy

	def fastmerge(self,img1,img2):
		img1_arr = np.asarray(img1)
		img2_arr = np.asarray(img2)
		# making both image shapes equal
		img2_arr = np.pad(img2_arr, ((0,img1_arr.shape[0] - img2_arr.shape[0]), (0,img1_arr.shape[1] - img2_arr.shape[1]), (0, 0)), 'constant')
		# merging MSB bits of cover image with LSB bits of input image
		out_arr = (img1_arr - img1_arr%16) + (img2_arr//16)
		return Image.fromarray(out_arr)


	def fastunmerge(self,img):
		img_arr = np.asarray(img)
		out_arr = (img_arr%16)*16 # Extracting LSB bits and coverting them to 8-bit value
		xs,ys,zs = np.where(out_arr!=0) # Finding boundary of hidden image
		out_arr = out_arr[min(xs):max(xs)+1,min(ys):max(ys)+1,min(zs):max(zs)+1]
		return Image.fromarray(out_arr)


	# --- Image Merge Function ---

	def merge(self,coverImage,realImage,passcode=None):
		coverImage = Image.open(coverImage)
		realImage = Image.open(realImage)
		if realImage.size[0] > coverImage.size[0] or realImage.size[1] > coverImage.size[1]:
			raise ValueError('input-image should be smaller than cover-image!')
		if(passcode == None):
			merged_image = self.fastmerge(coverImage,realImage)
		else:
			encrypted_image = self.encryptImage(realImage,passcode)
			merged_image = self.fastmerge(coverImage,encrypted_image)

		return merged_image


	# --- Image Unmerge Function ---

	def unmerge(self,image,passcode=None):
		if(passcode == None):
			decrypted_image = self.fastunmerge(Image.open(image))
		else:
			decoded_image = self.fastunmerge(Image.open(image))
			decrypted_image = self.decryptImage(decoded_image,passcode)
		
		return decrypted_image


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Image-2-Image Steganoraphy @author => Surya_T")
	parser.add_argument('process', type=str, help="merge | unmerge")
	parser.add_argument('--cover', type=str, help='cover image path')
	parser.add_argument('--input', type=str, help='input image path')
	parser.add_argument('--output', type=str, help='output image path')
	parser.add_argument('--password', type=str, help='encryption password')
	args = parser.parse_args()
	if(args.process=='merge'):
		if(args.cover==None or args.input==None):
			parser.error('merge requires --cover and --input arguments.')
		else:
			print('Started Merging Process...')
			merged_image = ImageStegano().merge(args.cover,args.input,args.password)
			if(args.output != None):
				out_path = Path(args.output).parents[0]
				out_name = Path(args.output).name.split('.')[0]+'.png'
			else:
				out_path = Path(args.cover).parents[0]
				out_name = Path(args.cover).name.split('.')[0]+'-'+Path(args.input).name.split('.')[0]+'-merged.png'
			output = str(out_path)+'/'+out_name
			merged_image.save(output)
			print('Merged Output Image : '+ output)
	elif(args.process=="unmerge"):
		if(args.input==None):
			parser.error('unmerge requires --input argument.')
		else:
			print('Started Unmerging Process...')
			decrypted_image = ImageStegano().unmerge(args.input,args.password)
			if(args.output != None):
				out_path = Path(args.output).parents[0]
				out_name = Path(args.output).name.split('.')[0]+'.png'
			else:
				out_path = Path(args.input).parents[0]
				out_name = Path(args.input).name.split('.')[0]+'-decrypted.png'
			output = str(out_path)+'/'+out_name
			decrypted_image.save(output)
			print('Decrypted Output Image : '+ output)
	else:
		parser.error('use either merge or unmerge method.')