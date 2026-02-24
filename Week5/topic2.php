<?php
$hptags = "magic,wizards,school,friendship";

$tagsArray = explode(",", $hptags);
// We can use foreach method to loop through the array.
echo "<ul>";
foreach ($tagsArray as $tag) {
echo "<li>$tag</li>";
}
echo "</ul>";
$favAuthors=["Stephen King","Jodi Pioult","Haruki Marakami"];
$favAuthorsDisp = implode(" | ", $favAuthors);
echo "<br> >h3>$favAuthorsDisp</h3>"
?>