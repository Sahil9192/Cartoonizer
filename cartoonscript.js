const imageUpload = document.getElementById("imageUpload");
const previewPlaceholder = document.getElementById("preview-placeholder");
const previewImg = document.getElementById("preview-img");
const cartoonOutput = document.getElementById("cartoon-output");
const processImageBtn = document.getElementById("processImage");

imageUpload.addEventListener("change", () => {
    const file = imageUpload.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = () => {
            previewPlaceholder.style.display = "none";
            previewImg.style.display = "block";
            previewImg.src = reader.result;
        };
        reader.readAsDataURL(file);
    }
});

processImageBtn.addEventListener("click", async () => {
    const lineSize = document.getElementById("lineSize").value;
    const blurValue = document.getElementById("blurValue").value;
    const numColors = document.getElementById("numColors").value;
    const file = imageUpload.files[0];

    if (!file) {
        alert("Please upload an image first!");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("line_size", lineSize);
    formData.append("blur_value", blurValue);
    formData.append("num_colors", numColors);

    try {
        const response = await fetch("/process_image", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) throw new Error("Image processing failed.");

        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);

        cartoonOutput.src = imageUrl;
        cartoonOutput.style.display = "block";
    } catch (error) {
        console.error(error);
        alert("Error processing image!");
    }
});
