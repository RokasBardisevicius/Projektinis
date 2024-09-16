import os
import random
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision.transforms import ToTensor
from PIL import Image
from config import Config

# Function to randomly crop low-resolution and high-resolution images
def random_crop(lowres_img, highres_img, hr_crop_size=Config.HIGH_RES, scale=Config.scale):
    """Randomly crop both low-resolution and high-resolution images."""
    lowres_crop_size = hr_crop_size // scale  # Crop size for low-resolution images

    # Determine random crop coordinates for the low-resolution image
    lowres_x = random.randint(0, lowres_img.size[0] - lowres_crop_size)
    lowres_y = random.randint(0, lowres_img.size[1] - lowres_crop_size)

    # Calculate corresponding coordinates for the high-resolution image
    highres_x = lowres_x * scale
    highres_y = lowres_y * scale

    # Crop the low-resolution and high-resolution images
    lowres_img_cropped = lowres_img.crop((lowres_x, lowres_y, lowres_x + lowres_crop_size, lowres_y + lowres_crop_size))
    highres_img_cropped = highres_img.crop((highres_x, highres_y, highres_x + hr_crop_size, highres_y + hr_crop_size))

    # Convert cropped images to tensor format
    lowres_img_cropped = ToTensor()(lowres_img_cropped)
    highres_img_cropped = ToTensor()(highres_img_cropped)

    return lowres_img_cropped, highres_img_cropped

# Custom dataset class that loads and preprocesses image pairs
class CustomDataset(Dataset):
    def __init__(self, lowres_dir, highres_dir, hr_crop_size=Config.HIGH_RES, scale=Config.scale):
        # Initialize dataset paths and settings
        self.lowres_dir = lowres_dir
        self.highres_dir = highres_dir
        self.image_files = [f for f in os.listdir(self.lowres_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        self.hr_crop_size = hr_crop_size
        self.scale = scale

        # Check if images exist in the directory
        if len(self.image_files) == 0:
            print(f"No image files found in {self.lowres_dir}. Please check the directory and file formats.")
        else:
            print(f"Found {len(self.image_files)} image files in {self.lowres_dir}")

    def __len__(self):
        # Return the number of image pairs
        return len(self.image_files)

    def __getitem__(self, idx):
        # Load low-resolution and high-resolution images
        lowres_path = os.path.join(self.lowres_dir, self.image_files[idx])
        highres_path = os.path.join(self.highres_dir, self.image_files[idx])

        try:
            lowres_image = Image.open(lowres_path).convert('RGB')
            highres_image = Image.open(highres_path).convert('RGB')
        except Exception as e:
            print(f"Error loading image {lowres_path} or {highres_path}: {e}")
            raise

        # Apply random cropping to images
        lowres_cropped, highres_cropped = random_crop(
            lowres_image, highres_image, hr_crop_size=self.hr_crop_size, scale=self.scale
        )

        return lowres_cropped, highres_cropped

# Function to load dataset and create a DataLoader
def load_dataset(lowres_dir, highres_dir, hr_crop_size=Config.HIGH_RES, scale=Config.scale, batch_size=Config.batch_size, shuffle=True, num_workers=4):
    # Create a dataset and return a DataLoader
    dataset = CustomDataset(lowres_dir, highres_dir, hr_crop_size, scale)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)

# Function to save model checkpoint
def save_checkpoint(model, optimizer, checkpoint_dir=Config.checkpoint_dir, epoch=0):
    # Create checkpoint directory if it doesn't exist
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir)
    checkpoint_path = os.path.join(checkpoint_dir, f'model_epoch_{epoch}_64_numfeatures.pth')
    # Save model and optimizer state
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'epoch': epoch
    }, checkpoint_path)
    print(f"Checkpoint saved at {checkpoint_path}")
