const imageUrlInput = document.getElementById("imageUrl");
const addImageBtn = document.getElementById("addImageBtn");
const deleteImageBtn = document.getElementById("deleteImageBtn");
const gallery = document.getElementById("gallery");

const titleInput = document.getElementById("titleInput"); 
const changeTitleBtn = document.getElementById("changeTitleBtn"); 
const galleryTitle = document.getElementById("galleryTitle");

addImageBtn.addEventListener("click", () => {
  const url = imageUrlInput.value;
  if (url) {
    const img = document.createElement("img");
    img.src = url;
    img.classList.add("fade-in");
    img.addEventListener("click", () => selectImage(img));
    gallery.appendChild(img);
    imageUrlInput.value = "";
    setTimeout(() => img.classList.remove("fade-in"), 500);
  }
});


function selectImage(img) {
  const allImages = gallery.querySelectorAll("img");
  allImages.forEach(i => i.classList.remove("selected"));
  img.classList.add("selected");
}

deleteImageBtn.addEventListener("click", () => {
  const selected = gallery.querySelector("img.selected");
  if (selected) {
    gallery.removeChild(selected);
  }
});

changeTitleBtn.addEventListener("click", () => { 
  const newTitle = titleInput.value.trim(); 
  if (newTitle) { galleryTitle.textContent = newTitle; 
  galleryTitle.classList.add("animate");  
  setTimeout(() => { galleryTitle.classList.remove("animate"); 
  }, 500); 
  titleInput.value = ""; 
  
  } 
});